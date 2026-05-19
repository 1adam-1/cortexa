import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';

export const EvaluationDashboard = ({ evaluationData }) => {
  // evaluationData = { faithfulness: 0.85, avg_rerank_score: 0.92, entailed: 4, total_sentences: 5, details: [...] }
  
  // Exemple de données si rien n'est passé en prop, pour tester le design :
  const data = evaluationData || {
    faithfulness: 0.75,
    avg_rerank_score: 0.88,
    entailed: 3,
    total_sentences: 4,
    details: [
      { sentence: "Le contexte est pertinent.", entailed: true, best_score: 0.95 },
      { sentence: "Ceci est une hallucination.", entailed: false, best_score: 0.23 },
    ]
  };

  const getScoreColor = (score) => {
    if (score >= 0.8) return "text-green-600 bg-green-50";
    if (score >= 0.5) return "text-yellow-600 bg-yellow-50";
    return "text-red-600 bg-red-50";
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold text-gray-800">Résultats d'Évaluation</h1>
      
      {/* SECTION 1 : Métriques Globales */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="shadow-sm border-t-4 border-t-blue-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Faithfulness Score</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {(data.faithfulness * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-gray-400 mt-1">Phrases supportées par le contexte</p>
          </CardContent>
        </Card>

        <Card className="shadow-sm border-t-4 border-t-purple-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Avg Rerank Score</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {data.avg_rerank_score.toFixed(3)}
            </div>
            <p className="text-xs text-gray-400 mt-1">Pertinence moyenne du contexte (Reranker)</p>
          </CardContent>
        </Card>

        <Card className="shadow-sm border-t-4 border-t-emerald-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Phrases Entailed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {data.entailed} <span className="text-lg text-gray-400">/ {data.total_sentences}</span>
            </div>
            <p className="text-xs text-gray-400 mt-1">Total des phrases validées</p>
          </CardContent>
        </Card>
      </div>

      <Separator className="my-6" />

      {/* SECTION 2 : Détails phrase par phrase */}
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="text-xl text-gray-800">Analyse détaillée phrase par phrase</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4 shadow-sm rounded-lg border bg-white overflow-hidden">
            <table className="w-full text-sm text-left">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 font-medium text-gray-900">Phrase générée</th>
                  <th className="px-6 py-3 font-medium text-gray-900 text-center">Statut (Entailed)</th>
                  <th className="px-6 py-3 font-medium text-gray-900 text-center">Best Score NLI</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.details && data.details.map((detail, index) => (
                  <tr key={index} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-800 break-words max-w-md">
                      {detail.sentence}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <Badge variant={detail.entailed ? 'default' : 'destructive'} 
                             className={detail.entailed ? 'bg-green-100 text-green-800 hover:bg-green-200' : 'bg-red-100 text-red-800 hover:bg-red-200'}>
                        {detail.entailed ? 'Supportée' : 'Hallucination'}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 text-center font-semibold">
                      <span className={"px-2 py-1 rounded-md $(detail.best_score)"}>
                        {detail.best_score.toFixed(3)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {(!data.details || data.details.length === 0) && (
              <div className="p-8 text-center text-gray-500">
                Aucun détail d'évaluation disponible pour cette génération.
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default EvaluationDashboard;
