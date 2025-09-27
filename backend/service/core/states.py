"""
State Definitions for LangGraph 0.6.x
Workflow data that changes during execution with reducer patterns
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from operator import add
from datetime import datetime


# ============ Custom Reducer Functions (Used Only) ============

def merge_dicts(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Merge dictionaries, b overwrites a"""
    if not a:
        return b or {}
    if not b:
        return a
    return {**a, **b}


def append_unique(a: List[Any], b: List[Any]) -> List[Any]:
    """Append only unique items to list"""
    if not a:
        a = []
    if not b:
        return a
    result = a.copy()
    for item in b:
        if item not in result:
            result.append(item)
    return result


# ============ Base State ============

class BaseState(TypedDict):
    """Base state for all workflows"""

    # Status tracking (overwrite)
    status: str  # pending, processing, completed, failed
    execution_step: str  # Current step in workflow

    # Error tracking (accumulate)
    errors: Annotated[List[str], add]  # Error messages

    # Timing (overwrite)
    start_time: Optional[str]
    end_time: Optional[str]


# ============ Subgraph States ============

class DataCollectionState(TypedDict):
    """State for data collection subgraph (PT Center)"""
    # Input
    query_params: Dict[str, Any]  # Parameters for data collection
    target_databases: List[str]  # Which databases to query

    # Collection results
    member_data: Annotated[List[Dict[str, Any]], add]  # Member information
    session_data: Annotated[List[Dict[str, Any]], add]  # PT session records
    workout_data: Annotated[List[Dict[str, Any]], add]  # Workout logs

    # Aggregated data
    aggregated_member: Annotated[Dict[str, Any], merge_dicts]  # Member stats
    aggregated_session: Annotated[Dict[str, Any], merge_dicts]  # Session stats
    aggregated_workout: Annotated[Dict[str, Any], merge_dicts]  # Workout stats

    # Status
    collection_status: str
    errors: Annotated[List[str], add]


class AnalysisState(TypedDict):
    """State for analysis subgraph (PT Center)"""
    # Input data (from data collection)
    member_data: List[Dict[str, Any]]  # Member profiles
    session_data: List[Dict[str, Any]]  # Session records
    workout_data: List[Dict[str, Any]]  # Workout logs

    # Analysis parameters
    analysis_type: str  # basic, progress, performance, comprehensive
    analysis_params: Dict[str, Any]

    # Analysis results
    basic_metrics: Annotated[Dict[str, Any], merge_dicts]  # Basic fitness metrics
    progress_analysis: Annotated[Dict[str, Any], merge_dicts]  # Progress tracking
    performance_analysis: Annotated[Dict[str, Any], merge_dicts]  # Performance metrics
    insights: Annotated[List[str], append_unique]  # Training insights

    # Final report
    analysis_report: Optional[Dict[str, Any]]

    # Status
    analysis_status: str
    errors: Annotated[List[str], add]


# ============ PT Session State (Active) ============

class PTSessionState(BaseState):
    """
    PT Session Management Agent State
    Workflow data that changes during execution for PT session management and member interaction
    """

    # === Input (overwrite) ===
    query: str  # User query (e.g., "오늘 PT 일정 알려줘", "회원 운동 기록 조회")
    member_id: Optional[str]  # Member identifier
    trainer_id: Optional[str]  # Trainer identifier
    session_type: Optional[str]  # Session type (e.g., "개인PT", "그룹PT", "상담")
    date_range: Optional[Dict[str, Any]]  # Date range (e.g., {"start": "2025-09-01", "end": "2025-09-30"})
    workout_type: Optional[str]  # Workout type (e.g., "근력", "유산소", "재활", "다이어트")

    # === Planning (overwrite) ===
    execution_plan: Optional[Dict[str, Any]]  # LLM generated plan

    # === Query Processing (overwrite) ===
    search_conditions: Dict[str, Any]  # Parsed search conditions from query
    generated_sql: Optional[str]  # Generated SQL

    # === Data Collection (accumulate) ===
    session_results: Annotated[List[Dict[str, Any]], add]  # PT session results

    # === Subgraph Results (merge) ===
    data_collection_result: Optional[Dict[str, Any]]  # From DataCollectionSubgraph
    analysis_result: Optional[Dict[str, Any]]  # From AnalysisSubgraph

    # === Aggregation (merge) ===
    collected_data: Annotated[Dict[str, Any], merge_dicts]  # From subgraphs
    execution_results: Annotated[Dict[str, Any], merge_dicts]  # Execution outcomes
    aggregated_data: Annotated[Dict[str, Any], merge_dicts]  # Aggregated metrics
    statistics: Annotated[Dict[str, float], merge_dicts]  # Statistical summaries

    # === Analysis (unique accumulate) ===
    insights: Annotated[List[str], append_unique]  # Workout insights and progress
    recommendations: Annotated[List[str], append_unique]  # Training recommendations

    # === Output (overwrite) ===
    briefing: Optional[str]  # Summary briefing for user
    final_report: Optional[Dict[str, Any]]  # Complete session report


class SupervisorState(BaseState):
    """
    Supervisor State for Main Orchestrator
    Manages intent analysis → planning → execution → evaluation workflow for PT Center
    """

    # === Input (overwrite) ===
    query: str  # User query

    # === Intent Analysis (overwrite) ===
    intent: Optional[Dict[str, Any]]  # Classified intent with extracted entities
    # Example: {
    #   "type": "schedule" | "workout_log" | "member_info" | "progress_analysis" | "booking",
    #   "member_id": "M12345",
    #   "trainer_id": "T001",
    #   "session_type": "개인PT",
    #   "date_range": {"start": "2025-09-01", "end": "2025-09-30"},
    #   "workout_type": "근력"
    # }

    # === Planning (overwrite) ===
    execution_plan: Optional[Dict[str, Any]]  # Agent execution plan
    # Example: {
    #   "strategy": "sequential" | "parallel" | "dag" | "swarm",
    #   "agents": [
    #     {"name": "schedule_manager", "order": 1, "params": {...}},
    #     {"name": "workout_analyzer", "order": 2, "params": {...}}
    #   ]
    # }

    # === Agent Execution (merge) ===
    agent_results: Annotated[Dict[str, Any], merge_dicts]  # Results from executed agents
    # Example: {
    #   "schedule_manager": {"status": "success", "data": [...]},
    #   "workout_analyzer": {"status": "success", "insights": [...]}
    # }

    # === Evaluation (overwrite) ===
    evaluation: Optional[Dict[str, Any]]  # Quality evaluation result
    # Example: {
    #   "quality_score": 0.85,
    #   "completeness": True,
    #   "needs_retry": False,
    #   "retry_agents": [],
    #   "feedback": "All session data collected successfully"
    # }

    # === Output (overwrite) ===
    final_output: Optional[Dict[str, Any]]  # Final formatted response
    # Example: {
    #   "answer": "오늘 PT 일정은...",
    #   "sessions": [...],
    #   "insights": [...],
    #   "metadata": {"total_sessions": 5, "completed": 3}
    # }


class DocumentState(BaseState):
    """
    State for document generation workflows (PT Center)
    """
    # Document specific fields
    doc_type: str  # Type of document (e.g., '운동처방전', '회원관리서', '진행보고서')
    doc_format: str  # Output format (markdown, html, text, word)
    title: str  # Document title
    input_data: Dict[str, Any]  # Input data for document generation
    template_id: str  # Template identifier
    sections: List[Dict[str, Any]]  # Document sections
    content: str  # Raw content
    formatted_content: str  # Formatted content
    document_metadata: Dict[str, Any]  # Document metadata
    final_document: Dict[str, Any]  # Final document with all details

    # Interactive processing fields
    user_query: Optional[str]  # Original user query
    query_analysis: Optional[Dict[str, Any]]  # Analysis result from LLM
    template_analysis: Optional[Dict[str, Any]]  # Template field analysis
    required_fields: Optional[List[Dict[str, Any]]]  # Required field definitions
    missing_fields: Optional[List[Dict[str, Any]]]  # Missing fields to collect
    collected_data: Annotated[Dict[str, Any], merge_dicts]  # Interactively collected data
    interaction_mode: Optional[str]  # interactive, batch, auto
    interaction_history: Annotated[List[Dict[str, Any]], add]  # History of interactions
    needs_user_input: bool  # Flag indicating if user input is needed
    current_prompt: Optional[str]  # Current prompt for user
    user_response: Optional[str]  # Latest user response


# ============ State Factory Functions ============

def create_pt_session_initial_state(**kwargs) -> Dict[str, Any]:
    """
    Create initial PTSessionState with defaults

    Args:
        **kwargs: Initial field values

    Returns:
        Initial state dictionary
    """
    return {
        # Status
        "status": "pending",
        "execution_step": "initializing",
        "errors": [],
        "start_time": datetime.now().isoformat(),

        # Input
        "query": kwargs.get("query", ""),
        "member_id": kwargs.get("member_id"),
        "trainer_id": kwargs.get("trainer_id"),
        "session_type": kwargs.get("session_type", "개인PT"),
        "date_range": kwargs.get("date_range"),
        "workout_type": kwargs.get("workout_type"),

        # Planning
        "execution_plan": None,

        # Query Processing
        "search_conditions": {},
        "generated_sql": None,

        # Data Collection
        "session_results": [],

        # Subgraph Results
        "data_collection_result": None,
        "analysis_result": None,

        # Aggregation
        "collected_data": {},
        "execution_results": {},
        "aggregated_data": {},
        "statistics": {},

        # Analysis
        "insights": [],
        "recommendations": [],

        # Output
        "briefing": None,
        "final_report": None,
        "end_time": None
    }


def create_supervisor_initial_state(**kwargs) -> Dict[str, Any]:
    """
    Create initial SupervisorState with defaults

    Args:
        **kwargs: Initial field values

    Returns:
        Initial state dictionary
    """
    return {
        # Status
        "status": "pending",
        "execution_step": "initializing",
        "errors": [],
        "start_time": datetime.now().isoformat(),

        # Input
        "query": kwargs.get("query", ""),

        # Intent Analysis
        "intent": None,

        # Planning
        "execution_plan": None,

        # Agent Execution
        "agent_results": {},

        # Evaluation
        "evaluation": None,

        # Output
        "final_output": None,
        "end_time": None
    }


def merge_state_updates(*updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple state updates

    Args:
        *updates: State update dictionaries

    Returns:
        Merged state update
    """
    result = {}
    for update in updates:
        for key, value in update.items():
            if value is not None:
                result[key] = value
    return result


def get_state_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get summary of current state

    Args:
        state: Current state

    Returns:
        Summary dictionary
    """
    return {
        "status": state.get("status"),
        "step": state.get("execution_step"),
        "errors_count": len(state.get("errors", [])),
        "has_results": bool(state.get("final_report") or state.get("formatted_result")),
        "data_collected": bool(state.get("collected_data") or state.get("sql_result")),
        "insights_count": len(state.get("insights", [])),
        "start_time": state.get("start_time"),
        "end_time": state.get("end_time")
    }