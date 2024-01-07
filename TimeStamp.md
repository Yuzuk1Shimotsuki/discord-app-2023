# Discord Timestamps
Discord timestamps can be useful for specifying a date/time across multiple users time zones. They work with the Unix Timestamp format and can be posted by regular users as well as bots and applications.

[The Epoch Unix Time Stamp Converter](https://www.unixtimestamp.com/) is a good way to quickly generate a timestamp. For the examples below I will be using the Time Stamp of `1543392060`, which represents `November 28th, 2018` at `09:01:00` hours for my local time zone (GMT+0100 Central European Standard Time).

## Formatting

|Style|Input|Output (12-hour clock)|Output (24-hour clock)
|--|--|--|--
|Default|`<t:1543392060>`|November 28, 2018 9:01 AM|28 November 2018 09:01
|Short Time|`<t:1543392060:t>`|9:01 AM|09:01
|Long Time|`<t:1543392060:T>`|9:01:00 AM|09:01:00
|Short Date|`<t:1543392060:d>`|11/28/2018|28/11/2018
|Long Date|`<t:1543392060:D>`|November 28, 2018|28 November 2018
|Short Date/Time|`<t:1543392060:f>`|November 28, 2018 9:01 AM|28 November 2018 09:01
|Long Date/Time|`<t:1543392060:F>`|Wednesday, November 28, 2018 9:01 AM|Wednesday, 28 November 2018 09:01
|Relative Time|`<t:1543392060:R>`|3 years ago|3 years ago

Whether your output is 12-hour or 24-hour depends on your Discord language setting. For example, if you have your Discord language set to `English, US 🇺🇸`, you will get a 12-hour output. If your Discord language is set to `English, UK 🇬🇧`, you will get a 24-hour output.

![](https://camo.githubusercontent.com/9ff9d6f08f6bbc03d7037ed60fd8e146fa4baa74c2c0b0a27307ca1849d2794b/68747470733a2f2f692e6c6576692e6c616e642f6650736935412f646972656374)

Sources: 

[Discord Developer Portal](https://discord.com/developers/docs/reference#message-formatting-timestamp-styles)

[Dan's Tools](https://www.unixtimestamp.com/)