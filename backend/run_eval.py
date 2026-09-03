import os
import json
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from app.agents.graph import agent_graph
from app.agents.state import AgentState

load_dotenv()

# Use a standard Generative LLM (Not a security classifier!)
# If 'llama-3.1-8b-instant' fails, try 'gemma2-9b-it' or 'qwen-qwq-32b'
judge_llm = ChatGroq(model="qwen/qwen3.8-27b", temperature=0.0)

def run_evaluation():
    print("--- Loading Ground Truth Dataset ---")
    with open("eval_dataset.json", "r") as f:
        test_data = json.load(f)

    results_table = []

    print("\n--- Running AI Agents & Grading Outputs ---")
    for item in test_data:
        print(f"\nProcessing {item['doc_id']}...")
        
        # A. Run the actual pipeline
        initial_state = AgentState(
            doc_id=item["doc_id"],
            document_content=item["document_content"],
            metadata={"source": "eval_dataset"}
        )
        final_state = agent_graph.invoke(initial_state)
        
        ai_answer = final_state.get("compliance_audit", "No audit generated.")
        citations = final_state.get("citations", [])
        context_text = "\n".join(citations)

        # B. The Prompt (Asking for Score and Reason explicitly)
        grading_prompt = f"""
        You are an expert AI Evaluator. Grade the following RAG pipeline output.
        You MUST respond using EXACTLY this format:
        
        Score: [a float between 0.0 and 1.0]
        Reason: [one short sentence explaining the score]

        [Question]: {item['question']}
        [Retrieved Context]: {context_text}
        [AI Answer]: {ai_answer}
        [Expected Answer]: {item['ground_truth_answer']}
        """

        # C. Get the response
        try:
            response = judge_llm.invoke(grading_prompt)
            response_text = str(response.content).strip()
            print(f"[DEBUG] Raw Judge Response:\n{response_text}") 
        except Exception as e:
            print(f"⚠️ LLM Error: {e}")
            response_text = ""

        # D. Robust Parsing for "Score:" and "Reason:"
        cp_score = 0.5
        faith_score = 0.5
        reasoning = "No reasoning provided."

        # Extract Score
        score_match = re.search(r'Score:\s*([0-9.]+)', response_text, re.IGNORECASE)
        if score_match:
            try:
                val = float(score_match.group(1))
                cp_score = val
                faith_score = val
            except ValueError:
                pass

        # Extract Reason
        reason_match = re.search(r'Reason:\s*(.*)', response_text, re.IGNORECASE | re.DOTALL)
        if reason_match:
            reasoning = reason_match.group(1).strip()

        results_table.append({
            "doc_id": item["doc_id"],
            "Context Precision": round(cp_score, 4),
            "Faithfulness": round(faith_score, 4),
            "Reasoning": reasoning
        })

    # 3. Print the Final Report Card
    print("\n" + "="*70)
    print("🛡️ CONTENTGUARD AI EVALUATION REPORT CARD (LLM-as-a-Judge)")
    print("="*70)
    for row in results_table:
        print(f"\n📄 Document: {row['doc_id']}")
        print(f"   ➡️ Context Precision: {row['Context Precision']}")
        print(f"   ➡️ Faithfulness:      {row['Faithfulness']}")
        print(f"   📝 Reasoning: {row['Reasoning']}")
    print("\n" + "="*70)

if __name__ == "__main__":
    run_evaluation()