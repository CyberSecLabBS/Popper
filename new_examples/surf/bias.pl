max_clauses(2).
max_vars(1).
max_body(2).

head_pred(surfing,1).
body_pred(pop,1).
body_pred(not_pop,1).
body_pred(windok,1).
body_pred(not_windok,1).
body_pred(sunshine,1).
body_pred(not_sunshine,1).

exclusive(pop,not_pop).
exclusive(windok,not_windok).
exclusive(sunshine,not_sunshine).
