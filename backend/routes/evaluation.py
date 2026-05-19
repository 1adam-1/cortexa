import json

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import and_, case, func

from entities.models import Evaluation, Generation, Session, db


evaluation_bp = Blueprint("evaluation", __name__)


def _parse_details(raw_details):
	if not raw_details:
		return []

	try:
		return json.loads(raw_details)
	except (TypeError, json.JSONDecodeError):
		return []



@evaluation_bp.route("/api/evaluations/dashboard", methods=["GET"])
@jwt_required()
def get_evaluation_dashboard_all():
	current_user_id = int(get_jwt_identity())

	sessions_count = Session.query.filter_by(id_etudiant=current_user_id).count()

	qa_generations = (
		db.session.query(func.count(Generation.id))
		.join(Session, Session.id == Generation.id_session)
		.filter(Session.id_etudiant == current_user_id, Generation.type == "Q/A")
		.scalar()
	)
	qa_generations = int(qa_generations or 0)

	low_case = case((Evaluation.faithfulness < 0.5, 1), else_=0)
	mid_case = case(
		(and_(Evaluation.faithfulness >= 0.5, Evaluation.faithfulness < 0.8), 1),
		else_=0,
	)
	high_case = case((Evaluation.faithfulness >= 0.8, 1), else_=0)

	(
		evaluations_count,
		avg_faithfulness,
		avg_rerank_score,
		total_sentences,
		total_entailed,
		last_updated,
		low_count,
		mid_count,
		high_count,
	) = (
		db.session.query(
			func.count(Evaluation.id),
			func.avg(Evaluation.faithfulness),
			func.avg(Evaluation.avg_rerank_score),
			func.sum(Evaluation.total_sentences),
			func.sum(Evaluation.entailed),
			func.max(Evaluation.created_at),
			func.sum(low_case),
			func.sum(mid_case),
			func.sum(high_case),
		)
		.join(Generation, Generation.id == Evaluation.id_generation)
		.join(Session, Session.id == Generation.id_session)
		.filter(Session.id_etudiant == current_user_id, Generation.type == "Q/A")
		.one()
	)

	count_value = int(evaluations_count or 0)
	avg_faithfulness_value = float(avg_faithfulness or 0.0)
	avg_rerank_value = float(avg_rerank_score or 0.0)
	total_sentences_value = int(total_sentences or 0)
	total_entailed_value = int(total_entailed or 0)
	hallucinations_value = max(0, total_sentences_value - total_entailed_value)

	coverage = round(count_value / qa_generations, 4) if qa_generations else 0.0

	return jsonify({
		"summary": {
			"sessions_count": sessions_count,
			"qa_generations": qa_generations,
			"evaluations_count": count_value,
			"coverage": coverage,
			"avg_faithfulness": round(avg_faithfulness_value, 4),
			"avg_rerank_score": round(avg_rerank_value, 4),
			"total_sentences": total_sentences_value,
			"total_entailed": total_entailed_value,
			"total_hallucinations": hallucinations_value,
			"last_updated": last_updated.isoformat() if last_updated else None,
		},
		"distribution": {
			"low": int(low_count or 0),
			"mid": int(mid_count or 0),
			"high": int(high_count or 0),
		},
	}), 200


