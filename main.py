import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from app.cli import main

if __name__ == "__main__":
    main()