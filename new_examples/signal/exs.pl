%for probfoil
base(signal(net)).
mode(signal(+)).
base(traffic(net)).
mode(traffic(+)).
base(humid(net)).
mode(humid(+)).
base(fast(net)).
learn(fast/1).

0.91::signal(1).
0.72::traffic(1).
0.23::humid(1).

0.31::signal(2).
0.79::traffic(2).
0.76::humid(2).

0.20::signal(3).
0.05::traffic(3).
0.15::humid(3).

0.84::signal(4).
0.77::traffic(4).
0.42::humid(4).

0.70::signal(5).
0.23::traffic(5).
0.01::humid(5).

0.95::signal(6).
0.10::traffic(6).
0.87::humidity(6).

0.55::signal(7).
0.12::traffic(7).
0.46::humid(7).

0.99::signal(8).
0.21::traffic(8).
0.75::humid(8).

0.92::signal(9).
0.47::traffic(9).
0.21::humid(9).

0.44::signal(10).
0.19::traffic(10).
0.67::humid(10).


0.2548::fast(1).
0.0651::fast(2).
0.19::fast(3).
0.1932::fast(4). 
0.539::fast(5).
0.855::fast(6).
0.484::fast(7).
0.7821::fast(8).
0.4876::fast(9).
0.3564::fast(10).