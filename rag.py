from langgraph.graph import START, StateGraph
from pinecone import Pinecone
from dotenv import load_dotenv
import os 
from langchain.chat_models import init_chat_model
from typing_extensions import List, TypedDict

load_dotenv()

pinecone_api_key = os.getenv("PICONE_API_KEY")
pc = Pinecone(api_key=pinecone_api_key)
index_name = "sotayhust"  
index = pc.Index(index_name)
llm = init_chat_model("gemini-2.5-flash", model_provider="google_genai")

def get_similar_doc(text, topk = 10):
    results = index.search(
        namespace="semantic_chunker", 
        query={
            "inputs": {"text": text}, 
            "top_k": topk
        },
        fields=["text"]
    )
    list_doc = []
    for doc in results["result"]['hits']:
        list_doc.append(doc['fields']['text'])
    return list_doc

class State(TypedDict):
    question: str
    context: List[str]
    answer: str
    
# Define application steps
def retrieve(state: State):
    retrieved_docs = get_similar_doc(state["question"])
    return {"context": retrieved_docs}

def get_prompt(question, context):
    return f"Bạn là một trợ lý ảo hỗ trợ sinh viên trong quá trình tìm kiếm thông tin từ sổ tay sinh viên. \
        Hãy trả lời câu hỏi: {question} dựa trên văn bản nguồn sau: {context}. Nếu như trong văn bản nguồn không \
        đủ thông tin, trả lời tôi không biết. Câu trả lời cần để ở dạng markdown. \
            Trả lời thẳng vào vấn đề, không cần thêm câu Dựa trên văn bản nguồn..."
        
def generate(state: State):
    docs_content = "\n\n".join(doc for doc in state["context"])
    messages = get_prompt(question = state["question"], context = docs_content)
    response = llm.invoke(messages)
    return {"answer": response.content}

graph_builder = StateGraph(State).add_sequence([retrieve, generate])
graph_builder.add_edge(START, "retrieve")
graph = graph_builder.compile()

def get_response(question):
    response = graph.invoke({"question": question})
    print(response["answer"])
    return response["answer"]

