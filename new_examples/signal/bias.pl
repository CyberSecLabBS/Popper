max_vars(3).
max_body(3).
max_clauses(2).

head_pred(fast,1).
body_pred(humid,1).
body_pred(signal,1).
body_pred(traffic,1).
body_pred(not_humid,1).
body_pred(low_signal,1).
body_pred(not_traffic,1).

exclusive(humid,not_humid).
exclusive(signal,low_signal).
exclusive(traffic,not_traffic).