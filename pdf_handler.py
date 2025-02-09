from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from llm_chains import load_vectordb, create_embeddings
import pypdfium2


def get_pdfs_texts(pdfs_bytes):
    return [extract_text_from_pdf(pdf_bytes) for pdf_bytes in pdfs_bytes]

def extract_text_from_pdf(pdf_bytes):
    pdf_file = pypdfium2.PdfDocument(pdf_bytes)
    
    #this is a multiple lines into one line function, can be split to be easier to read
    return "\n".join(pdf_file.get_page(page_number).get_textpage().get_text_range() for page_number in range(len(pdf_file)))


def get_text_chunks(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap =50, separators=["\n", "\n\n"])
    return splitter.split_text(text)

def get_document_chunks(text_list):
    documents = []
    for text in text_list:
            for chunk in get_text_chunks(text):
                    documents.append(Document(page_content= chunk))
    return documents

def add_documents_to_db(pdfs_bytes):
    texts = get_pdfs_texts(pdfs_bytes)
    documents = get_document_chunks(texts)
    embeddings = create_embeddings()
    vector_db = load_vectordb(embeddings)
    vector_db.add_documents(documents)