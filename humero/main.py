import os
from humero.config import settings
from semanticscholar import SemanticScholar
from humero.font_style import color
import copy
import pinecone
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.question_answering import load_qa_chain
from langchain.callbacks import get_openai_callback

# TODO: make these variables load from secrets file
os.environ["OPENAI_API_KEY"] = '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'
os.environ["PINECONE_INDEX_NAME"] = 'humero'
os.environ["PINECONE_API_KEY"] = '81e758f8-0626-4115-91ab-8c3e6423520d'
os.environ["PINECONE_API_ENV"] = 'us-west4-gcp-free'

class Humero:
    def __init__(self):
        # Define private variables
        #self.index_name = os.environ["PINECONE_INDEX_NAME"]

        self.embeddings = OpenAIEmbeddings()

        pinecone.init(
            api_key=os.environ["PINECONE_API_KEY"],
            environment=os.environ["PINECONE_API_ENV"]
        )
        self.index_name = os.environ["PINECONE_INDEX_NAME"]

        self.docsearch = Pinecone.from_documents(
            [], self.embeddings, index_name=self.index_name)

        llm = ChatOpenAI(temperature=0)
        self.chain = load_qa_chain(llm, chain_type="map_reduce")
    
    def add_paper_list(self, paper_ids: list[str], level: int = 1) -> None:
        """
            Add paper list to Pinecone index
        """
        # search papers
        sch = SemanticScholar()
        results = sch.get_papers(paper_ids, fields=['title', 'openAccessPdf', 'references', 'embedding'])
        
        papers = copy.deepcopy(results)
        # Print out added papers
        print(color.BOLD + "Adding papers:" + color.END)
        for paper in results:
            print("   -", paper.title)
            print("    ", len(paper.references), "references \n")

            # get references recursively
            # TODO: Some paperIds are None, is it possible to fetch it using other info?
            reference_ids = [reference.paperId for reference in paper.references if reference.paperId is not None]
            references = sch.get_papers(reference_ids, fields=['title', 'openAccessPdf', 'embedding'])
            papers += references

        # create embeddings and add to index
        indexed_papers = []
        combined_docs = []
        for paper in papers:
            # TODO: Not all papers have openAccessPDF, what other way could we add it?
            if paper.openAccessPdf:
                docs = self.process_pdf(paper.openAccessPdf['url'])
                if docs != []:
                    combined_docs += docs
                    indexed_papers.append(paper)

        print(color.BOLD + "Indexed papers:" + color.END)
        for paper in indexed_papers:
            print("   -", paper.title)

        # TODO: Documents already come with an embedding, how can we use them to save resources?
        # TODO: Add extra metadata: Actual openAccessPDF, title, author, etc.
        pinecone.init(
            api_key=os.environ["PINECONE_API_KEY"],
            environment=os.environ["PINECONE_API_ENV"]
        )
        self.docsearch = Pinecone.from_documents(
            combined_docs, self.embeddings, index_name=self.index_name)


    def ask(self, question: str) -> None:
        # Search up relevant documents
        docs = self.docsearch.similarity_search(question, k=10)

        # Print out sources
        print(color.BOLD + "Sources: " + color.END)
        sources = [doc.metadata for doc in docs]
        for source in sources:
            print("-----------------------------------------")
            print(color.BOLD + "Page: " + color.END + str(int(source["page"])))
            print(color.BOLD + "Document: " + color.END + source["source"])

        # Get result
        result = self.chain.run(input_documents=docs, question=question)
        print("-----------------------------------------")
        print(color.BOLD + "Answer:" + color.END + result)

    def process_pdf(self, filename: str):
        docs = []
        try:
            # TODO: many PDFs fail to load, find reliable way to access them
            loader = PyPDFLoader(filename)
            data = loader.load()

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=0)
            docs = text_splitter.split_documents(data)
        except Exception as e:
            print("Error loading", filename)

        return docs