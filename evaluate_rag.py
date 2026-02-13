"""
RAGAS Evaluation Script for RAG System

Evaluates the RAG system using RAGAS metrics:
- Faithfulness: How grounded is the answer in the retrieved context
- Answer Relevancy: How relevant is the answer to the question
- Context Recall: Is the ground truth present in retrieved context
- Context Precision: Are relevant contexts ranked higher

Generates comprehensive metrics for portfolio documentation.
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import time

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision
)
from datasets import Dataset

from omni_channel_ai_servicing.infrastructure.retrieval import Retriever
from omni_channel_ai_servicing.infrastructure.retrieval.vector_store import FAISSVectorStore
from omni_channel_ai_servicing.infrastructure.retrieval.embedding_service import EmbeddingService
from evaluation_dataset import get_evaluation_dataset


class RAGEvaluator:
    """Evaluate RAG system using RAGAS metrics."""
    
    def __init__(self):
        """Initialize RAG components."""
        print("Initializing RAG Evaluator...")
        
        # Initialize retrieval components
        index_dir = Path(__file__).parent / "faiss_index"
        self.embedding_service = EmbeddingService()
        self.vector_store = FAISSVectorStore(
            dimension=1536,
            index_path=str(index_dir)
        )
        self.vector_store.load(index_name="knowledge_base")
        
        self.retriever = Retriever(
            vector_store=self.vector_store,
            embedding_service=self.embedding_service
        )
        
        # Initialize LLM for generation
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
        print("✓ Retriever initialized")
        print("✓ LLM initialized (gpt-4o-mini)")
        
    def generate_answer(self, question: str, context: str) -> str:
        """Generate answer using LLM and retrieved context."""
        prompt = f"""You are a helpful customer service assistant. Use the provided context from our knowledge base to answer the user's question accurately.

Context from knowledge base:
{context}

User question: {question}

Instructions:
- Answer based on the context provided
- Be concise and helpful
- Include relevant policy details when applicable
- Don't make up information not in the context

Answer:"""
        
        response = self.llm.invoke(prompt)
        return response.content
    
    async def evaluate_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single query."""
        question = query_data["question"]
        ground_truth = query_data["ground_truth"]
        intent = query_data.get("intent", "general")
        
        print(f"\n  Query: {question[:60]}...")
        
        # Retrieve context
        start_time = time.time()
        results = self.retriever.retrieve(query=question, top_k=3, intent=intent)
        retrieval_time = time.time() - start_time
        
        # Format context
        contexts = [doc.page_content for doc in results]
        formatted_context = self.retriever.format_context(results)
        
        # Generate answer
        start_time = time.time()
        answer = self.generate_answer(question, formatted_context)
        generation_time = time.time() - start_time
        
        print(f"    Retrieved: {len(contexts)} docs ({retrieval_time*1000:.0f}ms)")
        print(f"    Generated: {len(answer)} chars ({generation_time*1000:.0f}ms)")
        
        return {
            "question": question,
            "answer": answer,
            "contexts": contexts,
            "ground_truth": ground_truth,
            "retrieval_time_ms": retrieval_time * 1000,
            "generation_time_ms": generation_time * 1000,
            "intent": intent
        }
    
    async def run_evaluation(self) -> Dict[str, Any]:
        """Run full RAGAS evaluation."""
        print("\n" + "="*80)
        print("Phase 4: RAGAS Evaluation")
        print("="*80)
        
        # Load dataset
        dataset = get_evaluation_dataset()
        print(f"\nDataset: {len(dataset)} queries")
        
        # Evaluate each query
        print("\nGenerating answers with RAG...")
        results = []
        for i, query_data in enumerate(dataset, 1):
            print(f"\n[{i}/{len(dataset)}]")
            result = await self.evaluate_query(query_data)
            results.append(result)
        
        # Prepare data for RAGAS
        print("\n" + "="*80)
        print("Running RAGAS Metrics...")
        print("="*80)
        
        ragas_data = {
            "question": [r["question"] for r in results],
            "answer": [r["answer"] for r in results],
            "contexts": [r["contexts"] for r in results],
            "ground_truth": [r["ground_truth"] for r in results]
        }
        
        ragas_dataset = Dataset.from_dict(ragas_data)
        
        # Run RAGAS evaluation
        print("\nEvaluating with RAGAS (this may take 1-2 minutes)...")
        
        ragas_results = evaluate(
            ragas_dataset,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_recall,
                context_precision
            ],
            llm=self.llm,
            embeddings=OpenAIEmbeddings()
        )
        
        # Extract metrics (RAGAS returns dict with lists)
        df = ragas_results.to_pandas()
        
        # Compile comprehensive results
        evaluation_results = {
            "timestamp": datetime.now().isoformat(),
            "dataset_size": len(dataset),
            "metrics": {
                "faithfulness": float(df["faithfulness"].mean()),
                "answer_relevancy": float(df["answer_relevancy"].mean()),
                "context_recall": float(df["context_recall"].mean()),
                "context_precision": float(df["context_precision"].mean())
            },
            "performance": {
                "avg_retrieval_time_ms": sum(r["retrieval_time_ms"] for r in results) / len(results),
                "avg_generation_time_ms": sum(r["generation_time_ms"] for r in results) / len(results),
                "avg_total_time_ms": sum(r["retrieval_time_ms"] + r["generation_time_ms"] for r in results) / len(results)
            },
            "tech_stack": {
                "vector_store": "FAISS",
                "embedding_model": "OpenAI text-embedding-3-small",
                "embedding_dimension": 1536,
                "llm": "GPT-4o-mini",
                "framework": "LangChain + LangGraph",
                "knowledge_base_size": 523,
                "knowledge_base_docs": 24
            },
            "individual_results": results,
            "ragas_full_results": ragas_results.to_pandas().to_dict('records')
        }
        
        return evaluation_results
    
    def print_results(self, results: Dict[str, Any]):
        """Print comprehensive results."""
        print("\n" + "="*80)
        print("RAGAS Evaluation Results")
        print("="*80)
        
        metrics = results["metrics"]
        print(f"\n📊 Metrics:")
        print(f"  Faithfulness:       {metrics['faithfulness']:.3f}")
        print(f"  Answer Relevancy:   {metrics['answer_relevancy']:.3f}")
        print(f"  Context Recall:     {metrics['context_recall']:.3f}")
        print(f"  Context Precision:  {metrics['context_precision']:.3f}")
        
        perf = results["performance"]
        print(f"\n⚡ Performance:")
        print(f"  Avg Retrieval:  {perf['avg_retrieval_time_ms']:.0f}ms")
        print(f"  Avg Generation: {perf['avg_generation_time_ms']:.0f}ms")
        print(f"  Avg Total:      {perf['avg_total_time_ms']:.0f}ms")
        
        tech = results["tech_stack"]
        print(f"\n🔧 Tech Stack:")
        print(f"  Vector Store:   {tech['vector_store']}")
        print(f"  Embeddings:     {tech['embedding_model']}")
        print(f"  LLM:            {tech['llm']}")
        print(f"  Framework:      {tech['framework']}")
        print(f"  KB Size:        {tech['knowledge_base_size']} chunks from {tech['knowledge_base_docs']} docs")
        
        print(f"\n📈 Dataset:")
        print(f"  Total Queries:  {results['dataset_size']}")
        
        # Sample answers
        print(f"\n📝 Sample Answers:")
        for i, result in enumerate(results["individual_results"][:3], 1):
            print(f"\n  [{i}] Q: {result['question'][:70]}...")
            print(f"      A: {result['answer'][:100]}...")
    
    def save_results(self, results: Dict[str, Any], output_dir: Path):
        """Save results to files."""
        output_dir.mkdir(exist_ok=True)
        
        # Save full JSON
        json_path = output_dir / "ragas_results.json"
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✓ Results saved to: {json_path}")
        
        # Save metrics summary
        summary_path = output_dir / "metrics_summary.txt"
        with open(summary_path, 'w') as f:
            f.write("RAGAS Evaluation Summary\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Faithfulness:      {results['metrics']['faithfulness']:.3f}\n")
            f.write(f"Answer Relevancy:  {results['metrics']['answer_relevancy']:.3f}\n")
            f.write(f"Context Recall:    {results['metrics']['context_recall']:.3f}\n")
            f.write(f"Context Precision: {results['metrics']['context_precision']:.3f}\n")
            f.write(f"\nAvg Latency: {results['performance']['avg_total_time_ms']:.0f}ms\n")
        print(f"✓ Summary saved to: {summary_path}")


async def main():
    """Run RAGAS evaluation."""
    try:
        evaluator = RAGEvaluator()
        
        # Run evaluation
        results = await evaluator.run_evaluation()
        
        # Print results
        evaluator.print_results(results)
        
        # Save results
        output_dir = Path(__file__).parent / "evaluation_results"
        evaluator.save_results(results, output_dir)
        
        print("\n" + "="*80)
        print("✅ Evaluation Complete!")
        print("="*80)
        
        # Check if results meet targets
        metrics = results["metrics"]
        targets_met = (
            metrics["faithfulness"] >= 0.80 and
            metrics["context_recall"] >= 0.75
        )
        
        if targets_met:
            print("\n🎉 Results meet target thresholds! Ready for portfolio.")
        else:
            print("\n⚠️  Some metrics below targets. Consider adding more context or refining queries.")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
