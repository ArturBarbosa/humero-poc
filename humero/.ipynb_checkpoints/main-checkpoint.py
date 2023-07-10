import os
from humero.config import settings
from semanticscholar import SemanticScholar
from humero.font_style import color

#os.environ["OPENAI_API_KEY"] = settings.openai_api_key
#os.environ["PINECONE_INDEX_NAME"] = settings.pinecone_index_name
#os.environ["PINECONE_API_KEY"] = settings.pinecone_api_key
#os.environ["PINECONE_API_ENV"] = settings.pinecone_api_env

class Humero:
    def __init__(self):
        # Define private variables
        #self.index_name = os.environ["PINECONE_INDEX_NAME"]

        pass
    
    def add_paper_list(self, paper_ids: list[str], level: int = 1) -> None:
        """
            Add paper list to Pinecone index
        """
        # search papers
        sch = SemanticScholar()
        results = sch.get_papers(paper_ids, fields=['title', 'openAccessPdf', 'references'])
        
        papers = results
        # Print out added papers
        print(color.BOLD + "Adding papers:" + color.END)
        for paper in results:
            print("   -", paper.title)
            print("    ", len(paper.references), "references \n")
            print(paper.references)

            # get references recursively
            reference_ids = [reference.paper_id for reference in paper.references]
            references = sch.get_papers(reference_ids, fields=['title', 'openAccessPdf'])
            papers += references

        # create embeddings and add to index
        for paper in papers:
            print(paper.title)

    def ask(question: str) -> None:
        pass