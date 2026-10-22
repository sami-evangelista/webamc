import datetime
import typing as tp
import typing_extensions as tp_ext


exam_status_t = tp.Literal[
    "finished",
    "in-progress",
    "upcoming"
]
exam_student_status_t = tp.Literal[
    "inactive",
    "not-started",
    "online"
]
student_monitoring_t = tp_ext.TypedDict("student_monitoring_t", {
    "reg_id": int,
    "usr_name": str,
    "usr_fst_name": str,
    "status": exam_student_status_t,
    "last_seen": datetime.datetime | None,
    "answered_count": int,
    "total_questions": int,
    "score": float
})
exam_monitoring_t = tp_ext.TypedDict("exam_monitoring_t", {
    "status": exam_status_t,
    "start": datetime.datetime,
    "end": datetime.datetime,
    "students": list[student_monitoring_t]
})
