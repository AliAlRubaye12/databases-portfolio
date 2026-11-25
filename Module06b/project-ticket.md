# Project ticket — candidates for the final-project kickoff

Back to [Module 6b](README.md). Three candidates, as the workbook suggests; the Project Team picks one (or none) at the kickoff.

## 1. The lab-equipment booking sheet

**Person:** the lab assistant who lends out equipment (laptops, sensors, cameras) at the faculty.
**Problem:** today it is a paper list — nobody knows what is overdue until a course needs it. The data decides *who gets a reminder today*.
**First query:** *"Which items are overdue, who has them, and since when?"*
**Data source:** generated reproducibly with a script (items, people, loans with due dates); later a simple form for real loans.

## 2. The student-café stock

**Person:** the student who runs the café's weekly order.
**Problem:** too much milk goes off, too little coffee arrives. The data decides *what to order this week*.
**First query:** *"Average daily use per product over the last four weeks, and how many days the current stock lasts."*
**Data source:** a generated sales and delivery log (seeded random, like Module 1's telemetry), replaceable by the till's CSV export.

## 3. The shared-flat energy meter

**Person:** a flatmate who pays the electricity bill and wants a fair split.
**Problem:** the bill is shared equally, but usage is not. The data decides *how to split the bill*.
**First query:** *"kWh per room per week, and each room's share of the month's bill."*
**Data source:** generated smart-plug readings every minute (the same pattern as Module 1), or a real smart-plug CSV export.
