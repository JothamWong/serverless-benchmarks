# Timing definitions

client_begin: when the client made the request
client_end: when the client received the response
output_begin: when the worker started function
output_end: when the worker finished function, havent transmitted

schedule_duration: start of earliest client_begin to end of client_end

In non-blocking, schedule duration is lower
In blocking, schedule duration is higher
Need to account that blocking, schedule is essentially end-to-end latency

I made some mistakes with the time logging for non-blocking
I did not track the client_begin and client_end properly