from unstructured.partition.pdf import partition_pdf

elements = partition_pdf("ml.pdf")

for el in elements:
    print(el, "*****************\n\n")