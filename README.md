# whats-the-price-for-the-milk

Monitor prices for a certain piece of milk.

A pipeline checks the price daily.

It can be configured to _fail_ if it is below a certain value, then github sends
out an email alert.
It can also be configured to send a WhatsApp notification using
[callmebot.com](https://www.callmebot.com/blog/free-api-whatsapp-messages/)
if the price is below a certain value.
