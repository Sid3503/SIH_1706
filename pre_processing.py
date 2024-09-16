# pdf_processing.py
import os
from PyPDF2 import PdfReader
from flask import Flask, request, render_template, jsonify
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from langchain.memory import ConversationBufferMemory
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceInstructEmbeddings
from langchain_community.llms import HuggingFaceHub
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_pdf_text(pdf_path):
    """Extract text from the PDF."""
    text = ""
    pdf_reader = PdfReader(pdf_path)
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def get_text_chunks(text):
    """Split text into chunks for processing."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_text(text)
    return chunks

def load_vector_store():
    """Load or initialize FAISS vector store."""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    if os.path.exists("faiss_index"):
        # Load the vector store from the saved index
        return FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    else:
        raise ValueError("Vector store not found. Please upload and process a PDF first.")

def get_conversational_chain():
    """Initialize the conversational chain using Google Generative AI."""
    prompt_template = """
    Based on the following context items from the organizational document, please provide a comprehensive summary of the answer related to context...
    The user question can be anything like a word related or in the pdf, be robust to extract relevant answers according to given word or words.
    Sometimes the user would just give some word or 2-3 words as question.
    So extract answers from context according to those words.
    {context}
    User query: {question}
    Answer:
    """
    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.5)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

def summarize_data(pdf_path):
    """Summarize content from PDF."""
    text_data = get_pdf_text(pdf_path)
    summray_type = request.form.get('summary_type')
    if summray_type == "brief":
        default_prompt = "Summarize and extract text (keyword information) from documents relevant to organizational needs in brief in 5-6 lines mentioning about company name and core components of the pdf."
        model = genai.GenerativeModel("gemini-1.5-flash")
        response_stream = model.generate_content(
            [default_prompt, text_data],
            generation_config=genai.types.GenerationConfig(temperature=0.7),
            stream=True
        )
        summary_output = ""
        for message in response_stream:
            summary_output += message.text
        response_stream.resolve()
        return summary_output
    
    else:
        default_prompt = "Summarize and extract text (keyword information) from documents relevant to organizational needs."
        model = genai.GenerativeModel("gemini-1.5-flash")
        response_stream = model.generate_content(
            [default_prompt, text_data],
            generation_config=genai.types.GenerationConfig(temperature=0.7),
            stream=True
        )
        summary_output = ""
        for message in response_stream:
            summary_output += message.text
        response_stream.resolve()
        return summary_output

def user_input(user_question):
    """Handle user queries using a conversational chain."""
    try:
        new_db = load_vector_store()
        docs = new_db.similarity_search(user_question)
        chain = get_conversational_chain()
        response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
        return response["output_text"]
    except Exception as e:  
        return f"Error: {str(e)}"
    

def fetch_org_info_from_genai(filepath):
   
    text_data = get_pdf_text(filepath)
    
    default_prompt = (
        "Extract the organization name and relevant details from the following document. "
        "Mention the core components of the organization discussed in the PDF."
    )
    
    model = genai.GenerativeModel("gemini-1.5-flash")

    response_stream = model.generate_content(
        [default_prompt, text_data],
        generation_config=genai.types.GenerationConfig(temperature=0.7),
        stream=True
    )
    org_info_output = ""
    for message in response_stream:
        if hasattr(message, 'text'):
            org_info_output += message.text
        else:
            raise ValueError("No valid text in the response part.")
    
    response_stream.resolve()

    return org_info_output
