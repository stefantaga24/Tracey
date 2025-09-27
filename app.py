import streamlit as st
from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_google_vertexai import ChatVertexAI
from utils import visualize_graph_documents
from extract_names import get_normalized_path
from typing import List, Optional
from langchain_community.graphs.graph_document import GraphDocument, Node, Relationship
from pathlib import Path
import json

# --- Page Configuration ---
st.set_page_config(
    page_title="Knowledge Graph Builder 🧠",
    page_icon="🕸️",
    layout="wide"
)

# --- Static Definitions & Helper Functions ---
ALLOWED_NODES = ["Person", "Organization", "Government body", "Company", "Political Party", "Location"]
OUTPUT_DIR = Path("output_graphs")
JSON_DIR = Path("extracted_graphs")

# Create output directories if they don't exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
JSON_DIR.mkdir(parents=True, exist_ok=True)
def display_visualization_graph_in_streamlit(path: str):
    try:
        html_content = Path(path).read_text(encoding="utf-8")
        
        # Display the HTML content using the Streamlit components API
        import streamlit.components.v1 as components
        
        st.subheader("Interactive Visualization")
        # You may need to adjust the height based on your visualization library
        components.html(html_content, height=800, scrolling=True) 
        
    except FileNotFoundError:
        st.error(f"Visualization file not found at: {path}")
def display_current_graph_state():
    # --- Display Current Graph State ---
    st.divider()
    st.header("Current Knowledge Graph State")

    if not st.session_state.graph.nodes:
        st.info("The knowledge graph is currently empty. Upload files or process a folder to begin.")
    else:
        num_nodes = len(st.session_state.graph.nodes)
        num_rels = len(st.session_state.graph.relationships)
        
        st.metric("Total Nodes", num_nodes)
        st.metric("Total Relationships", num_rels)

        # ... Inside the section where you display the graph state ...

    if st.session_state.last_viz_path:
        display_visualization_graph_in_streamlit(st.session_state.last_viz_path)
        with st.expander("Show Raw Graph Data (JSON)"):
            st.json(st.session_state.graph.model_dump())
            
def enhance_graph_prompt(initial_documents: List[Document], all_nodes: List[Node], all_relationships: List[Relationship]) -> str:
    """Creates the prompt for the LLM to enhance an existing graph."""
    return (
        f"Original Text:\n{initial_documents[0].page_content}\n\n"
        f"We have already extracted the following graph. Review it and extract "
        f"any additional nodes, relationships and properties from the original text that might be missing.\n\n"
        f"Current Nodes:\n{[node.model_dump() for node in all_nodes]}\n\n"
        f"Current Relationships:\n{[rel.model_dump() for rel in all_relationships]}"
    )

def iterative_graph_development(transformer: LLMGraphTransformer, number_iterations: int, initial_documents: List[Document],
                                  initial_nodes: List[Node], initial_relationships: List[Relationship]) -> GraphDocument:
    """
    Performs iterative graph extraction and refinement.
    This is the synchronous version of the original async function.
    """
    all_nodes: List[Node] = list(initial_nodes)
    all_relationships: List[Relationship] = list(initial_relationships)
    current_documents = initial_documents
    initial_page_content = Document(page_content=initial_documents[0].page_content)

    for i in range(number_iterations):
        st.info(f"--- Iteration {i+1} of {number_iterations} ---")
        # Convert documents to a graph
        graph_documents = transformer.convert_to_graph_documents(current_documents)
        
        if graph_documents:
            graph = graph_documents[0]
            all_nodes.extend(graph.nodes)
            all_relationships.extend(graph.relationships)
            
            # Create a new prompt for the next iteration
            updated_content = enhance_graph_prompt(initial_documents, all_nodes, all_relationships)
            current_documents = [Document(page_content=updated_content)]
        else:
            st.warning(f"No new graph elements found in iteration {i+1}. Stopping early.")
            break

    # De-duplicate nodes and relationships
    unique_nodes = list({node.id: node for node in all_nodes}.values())
    unique_rels = [rel for i, rel in enumerate(all_relationships) if rel not in all_relationships[:i]]
    
    return GraphDocument(nodes=unique_nodes, relationships=unique_rels, source=initial_page_content)

# --- Streamlit UI ---

st.title("Interactive Knowledge Graph Builder 🕸️")
st.markdown("Upload text files sequentially or process an entire folder to build and visualize a knowledge graph.")

# --- Session State Initialization ---
if 'graph' not in st.session_state:
    st.session_state.graph = GraphDocument(nodes=[], relationships=[], source=Document(page_content=""))
    st.session_state.last_viz_path = ""

# --- Sidebar for Configuration ---
with st.sidebar:
    st.header("⚙️ Configuration")
    project_id = st.text_input("Google Cloud Project ID", placeholder="your-gcp-project-id")
    model_name = st.text_input("Vertex AI Model Name", "gemini-2.0-flash")
    iteration_number = st.slider("Number of Refinement Iterations", 1, 5, 2)
    
    if st.button("Reset Knowledge Graph", use_container_width=True):
        st.session_state.graph = GraphDocument(nodes=[], relationships=[], source=Document(page_content=""))
        st.session_state.last_viz_path = ""
        st.success("Graph has been reset.")

if not project_id or not model_name:
    st.warning("Please enter your Google Cloud Project ID and a Model Name in the sidebar to begin.")
    st.stop()

# --- Caching the LLM and Transformer instances ---
@st.cache_resource
def get_llm_transformer(project_id, model_name):
    llm = ChatVertexAI(model_name=model_name, project=project_id, location='global')
    transformer = LLMGraphTransformer(
        llm=llm,
        allowed_nodes=ALLOWED_NODES,
        node_properties=True,
        relationship_properties=True
    )
    return transformer

transformer = get_llm_transformer(project_id, model_name)

# --- Main UI Tabs ---
tab1, tab2, tab3 = st.tabs(["📄 Upload Files Sequentially", "📂 Process a Folder", "View 50 video visualization"])

with tab1:
    st.subheader("Incrementally add files to the graph")
    uploaded_files = st.file_uploader(
        "Upload one or more text files",
        type=['txt'],
        accept_multiple_files=True
    )

    if uploaded_files:
        if st.button("Process Uploaded Files", use_container_width=True, type="primary"):
            for uploaded_file in uploaded_files:
                file_content = uploaded_file.getvalue().decode("utf-8")
                doc = Document(page_content=file_content)
                norm_path = get_normalized_path(uploaded_file.name)
                
                with st.spinner(f"Processing `{uploaded_file.name}`... This may take a moment."):
                    # The current graph state is passed for enhancement
                    newly_extracted_graph = iterative_graph_development(
                        transformer, iteration_number, [doc],
                        st.session_state.graph.nodes, st.session_state.graph.relationships
                    )
                    
                    # Update the graph in session state
                    st.session_state.graph = newly_extracted_graph

            st.success("All uploaded files processed!")
            
            # --- Visualize and Save the final combined graph ---
            final_path_name = "sequential_upload_graph"
            html_path = OUTPUT_DIR / f"{final_path_name}.html"
            json_path = JSON_DIR / f"{final_path_name}.json"
            
            visualize_graph_documents([st.session_state.graph], output_filename=str(html_path))
            st.session_state.last_viz_path = str(html_path)
            
            with open(json_path, 'w') as f:
                json.dump(st.session_state.graph.model_dump(), f)
    display_current_graph_state()

with tab2:
    st.subheader("Build a graph from all text files in a folder")
    folder_path = st.text_input("Enter the path to a local folder:", placeholder="e.g., C:/Users/YourUser/Documents/transcripts")

    if st.button("Process Folder", use_container_width=True, type="primary"):
        if folder_path and Path(folder_path).is_dir():
            source_path = Path(folder_path)
            txt_files = list(source_path.glob("*.txt"))

            if not txt_files:
                st.error(f"No `.txt` files found in `{folder_path}`.")
            else:
                with st.spinner(f"Reading {len(txt_files)} files from folder..."):
                    combined_content = []
                    for file in txt_files:
                        combined_content.append(file.read_text(encoding='utf-8'))
                    
                    full_document = Document(page_content="\n\n---\n\n".join(combined_content))

                with st.spinner(f"Building graph from all {len(txt_files)} files... This will take some time."):
                     # Start with an empty graph and build from the combined document
                    final_graph = iterative_graph_development(
                        transformer, iteration_number, [full_document], [], []
                    )
                    st.session_state.graph = final_graph
                    st.success("Folder processed successfully!")
                    
                    # --- Visualize and Save ---
                    final_path_name = f"folder_graph_{source_path.name}"
                    html_path = OUTPUT_DIR / f"{final_path_name}.html"
                    json_path = JSON_DIR / f"{final_path_name}.json"
                    
                    visualize_graph_documents([st.session_state.graph], output_filename=str(html_path))
                    st.session_state.last_viz_path = str(html_path)

                    with open(json_path, 'w') as f:
                        json.dump(st.session_state.graph.model_dump(), f)
        else:
            st.error("Please enter a valid folder path.")
    display_current_graph_state()
with tab3:
    display_visualization_graph_in_streamlit("the_big_answer_one_iteration.html")