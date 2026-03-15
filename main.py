import os
import argparse
import pickle
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import pdfplumber
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from sentence_transformers import CrossEncoder
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from app.cli import main


if __name__ == "__main__":
    main()