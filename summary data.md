Excel Column Reference Table
Excel Col	Col #	Header Name
B	          2	       Date
C	          3	       Client Type
D	          4	       Future Index Long
E	          5	       Future Index Short
F	          6	       Future Stock Long
G	          7	       Future Stock Short
H	          8	       Option Index Call Long
I	          9	       Option Index Put Long
J	         10	       Option Index Call Short
K	         11	       Option Index Put Short
L	         12	       Option Stock Call Long
M	         13	       Option Stock Put Long
N	         14	       Option Stock Call Short
O	         15	       Option Stock Put Short
P	         16	       Total Long Contracts
Q	         17	       Total Short Contracts

Client Type Row Reference
Date	Client Type	Excel Row No.
5.12.25	      Client	     6
               DII	         7
               FII	         8
               Pro	         9
               TOTAL	       10
4.12.25	      Client	     11
               DII	         12
               FII	         13
               Pro	         14



SECTION: OPTION (Excel columns 18-24)

Column 18 (R) - NET DIFF
Header: NET DIFF
Excel Formula: =AW6-AX6
Description: NET CALL minus NET PUT. Represents the difference between the Change in Call Index and the Change in Put Index.
Python:df['NET DIFF'] = df['Call Index CoC'] - df['Put Index CoC']

Column 19 (AS) - ROC
Header: ROC
Excel Formula: =R6-R11
Description: Current NET DIFF minus Previous Day NET DIFF (Row 11 corresponds to the same client type from the previous date).
Python:Assumes df is sorted by Date (desc) and grouped by Client Type
df['Option ROC'] = df.groupby('Client Type')['NET DIFF'].diff(periods=-1)

Column 20 (AT) - call Index
Header: ABSULATE CHANGE > call Index
Excel Formula: =H6-J6
Description: Option Index Call Long minus Option Index Call Short. Represents the net Call contracts held.
Python:df['Absolute Change Call Index'] = df['Option Index Call Long'] - df['Option Index Call Short']

Column 21 (AU) - Put Index
Header: ABSULATE CHANGE > Put Index
Excel Formula: =I6-K6
Description: Option Index Put Long minus Option Index Put Short. Represents the net Put contracts held.
Python:df['Absolute Change Put Index'] = df['Option Index Put Long'] - df['Option Index Put Short']

Column 22 (AV) - OPTION NET
Header: OPTION > NET
Excel Formula: =(H6+K6)-(I6+J6)
Description: (Option Index Call Long + Option Index Put Short) minus (Option Index Put Long + Option Index Call Short). This calculates the total Bullish positions minus the total Bearish positions.
Python:df['Option NET'] = (df['Option Index Call Long'] + df['Option Index Put Short']) - (df['Option Index Put Long'] + df['Option Index Call Short'])

Column 23 (AW) - NET CALL
Header: NET CALL
Excel Formula: =AT6-AT11
Description: Current Call Index (Col AT) minus Previous Day Call Index (Row 11). This is the Change of Character (CoC) for Calls.
Python:df['Call Index CoC'] = df.groupby('Client Type')['Absolute Change Call Index'].diff(periods=-1)

Column 24 (AX) - NET PUT
Header: NET PUT
Excel Formula: =AU6-AU11
Description: Current Put Index (Col AU) minus Previous Day Put Index (Row 11). This is the Change of Character (CoC) for Puts.
Python:df['Put Index CoC'] = df.groupby('Client Type')['Absolute Change Put Index'].diff(periods=-1)


SECTION: FUTURE (Excel columns 25-31)

Column 25 (AY) - FUTURE NET
Header: FUTURE > NET
Excel Formula: =D6-E6
Description: Future Index Long minus Future Index Short. Represents the net Future contracts held.
Python:df['Future Index Net'] = df['Future Index Long'] - df['Future Index Short']

Column 26 (AZ) - FUTURE ROC
Header: ROC
Excel Formula: =AY6-AY11
Description: Current Future NET minus Previous Day Future NET (Row 11 corresponds to the same client type from the previous date).
Python:df['Future Index CoC'] = df.groupby('Client Type')['Future Index Net'].diff(periods=-1)

Column 27 (BA) - ABSULATE CHANGE LONG
Header: ABSULATE CHANGE > LONG
Excel Formula: =D6-D11
Description: Current Future Index Long minus Previous Day Future Index Long. Represents the net Future contracts held.
Python:df['Future Long Change'] = df.groupby('Client Type')['Future Index Long'].diff(periods=-1)

Column 28 (BB) - ABSULATE CHANGE SHORT
Header: ABSULATE CHANGE > SHORT
Excel Formula: =E6-E11
Description: Current Future Index Short minus Previous Day Future Index Short. Represents the net Future contracts held.
Python:df['Future Short Change'] = df.groupby('Client Type')['Future Index Short'].diff(periods=-1)

Column 29 (BC) - L/S RATIO
Header: L/S RATIO
Excel Formula: =D6/E6
Description: Future Index Long divided by Future Index Short. Represents the ratio of Future contracts held.
Python:df['Future L/S'] = df['Future Index Long'] / df['Future Index Short']

Column 30 (BD) - LONG %
Header: LONG > %
Excel Formula: =BA6/D11
Description: ABSULATE CHANGE LONG divided by Previous Day Future Index Long (percentage change).
Python:df['Future Long %'] = df['Future Long Change'] / df.groupby('Client Type')['Future Index Long'].shift(-1)

Column 31 (BE) - SHORT %
Header: SHORT > %
Excel Formula: =BB6/E11
Description: ABSULATE CHANGE SHORT divided by Previous Day Future Index Short (percentage change).
Python:df['Future Short %'] = df['Future Short Change'] / df.groupby('Client Type')['Future Index Short'].shift(-1)


SECTION: FUTURE STOCK (Excel columns 32-38)

Column 32 (BF) - FUTURE STOCK NET
Header: FUTURE > NET
Excel Formula: =F6-G6
Description: Future Stock Long minus Future Stock Short. Represents the net Future Stock contracts held.
Python:df['Future Stock Net'] = df['Future Stock Long'] - df['Future Stock Short']

Column 33 (BG) - FUTURE STOCK ROC
Header: ROC
Excel Formula: =BF6-BF11
Description: Current Future Stock NET minus Previous Day Future Stock NET (Row 11 corresponds to the same client type from the previous date).
Python:df['Future Stock CoC'] = df.groupby('Client Type')['Future Stock Net'].diff(periods=-1)

Column 34 (BH) - ABSULATE CHANGE LONG
Header: ABSULATE CHANGE > LONG
Excel Formula: =F6-F11
Description: Current Future Stock Long minus Previous Day Future Stock Long. Represents the net Future Stock contracts held.
Python:df['Future Stock Long Change'] = df.groupby('Client Type')['Future Stock Long'].diff(periods=-1)

Column 35 (BI) - ABSULATE CHANGE SHORT
Header: ABSULATE CHANGE > SHORT
Excel Formula: =G6-G11
Description: Current Future Stock Short minus Previous Day Future Stock Short. Represents the net Future Stock contracts held.
Python:df['Future Stock Short Change'] = df.groupby('Client Type')['Future Stock Short'].diff(periods=-1)

Column 36 (BJ) - L/S RATIO
Header: L/S RATIO
Excel Formula: =F6/G6
Description: Future Stock Long divided by Future Stock Short. Represents the ratio of Future Stock contracts held.
Python:df['Future Stock L/S'] = df['Future Stock Long'] / df['Future Stock Short']

Column 37 (BK) - LONG %
Header: LONG > %
Excel Formula: =BH6/F11
Description: ABSULATE CHANGE LONG divided by Previous Day Future Stock Long (percentage change).
Python:df['Future Stock Long %'] = df['Future Stock Long Change'] / df.groupby('Client Type')['Future Stock Long'].shift(-1)

Column 38 (BL) - SHORT %
Header: SHORT > %
Excel Formula: =BI6/G11
Description: ABSULATE CHANGE SHORT divided by Previous Day Future Stock Short (percentage change).
Python:df['Future Stock Short %'] = df['Future Stock Short Change'] / df.groupby('Client Type')['Future Stock Short'].shift(-1)

SECTION: NIFTY & FUTURE RATIOS (Excel columns 39-)

Column 39 (BN) - NIFTY DIFF
Header: NIFTY > difff
Excel Formula: =BP6-BP11
Description: Current Day Nifty Spot minus Previous Day Nifty Spot.
Python: df['Nifty Diff'] = df.groupby('Client Type')['Nifty Spot'].diff(periods=-1)

Column 40 (BP) - NIFTY SPOT (Input)
Header: NIFTY > spot
Excel Formula: INPUT FIELD (e.g., 26186)
Description: User provides the closing price of NIFTY for that date.
Python: df['Nifty Spot'] (This data must be supplied/merged into the dataframe based on Date)

Column 41 (BQ) - FUTURE TOTAL LONG %
Header: FUTURE > TOTAL LONG %
Excel Formula: =D6/D10 (where D10 is the TOTAL row for that specific date)
Description: Client's Long Future Index contracts divided by the Grand Total of Long Future Index contracts for that day.
Python:df['Future Total Long %'] = df['Future Index Long'] / df.groupby('Date')['Future Index Long'].transform('sum')

Column 42 (BR) - FUTURE TOTAL SHORT %
Header: FUTURE > TOTAL SHORT %
Excel Formula: =E6/E10 (where E10 is the TOTAL row for that specific date)
Description: Client's Short Future Index contracts divided by the Grand Total of Short Future Index contracts for that day.
Python:
df['Future Total Short %'] = df['Future Index Short'] / df.groupby('Date')['Future Index Short'].transform('sum')

--------------------------------------------------------------------------
LIST OF THE INPUTS USER NEED TO PROVIDE 

1. Raw Data (The Main Table)
You need to provide a dataset (CSV or Excel) containing the following columns for every Date and Client Type (Client, DII, FII, Pro):
Date
Client Type
Future Index Long
Future Index Short
Future Stock Long
Future Stock Short
Option Index Call Long
Option Index Put Long
Option Index Call Short
Option Index Put Short
Option Stock Call Long
Option Stock Put Long
Option Stock Call Short
Option Stock Put Short
Total Long Contracts (Optional - can be calculated, but appears in your raw data)
Total Short Contracts (Optional - can be calculated, but appears in your raw data)

2. Manual Input Field
There is one specific field you must enter manually for each date:
Nifty Spot Price: (Column BP)
You must input the closing price of NIFTY for each specific date (e.g., 26186).
Why? This is required to calculate the "Nifty Diff" (Difference between current and previous day's spot price).

3. Structural Requirements
For the Excel formulas to work exactly as written (referencing specific rows like D10), your input data must include a TOTAL row for each date.
Required Rows per Date:
Client
DII
FII
Pro
TOTAL (Sum of the above 4)
Summary: You give the Daily Participant Data + the Nifty Spot Price. The sheet calculates everything else.

------------------------------------------------------------------------------

