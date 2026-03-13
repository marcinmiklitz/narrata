# narrata CLI demo
# Record with: vhs assets/demo.tape

Output assets/demo.gif

Set Shell "zsh"
Set FontSize 13
Set Width 960
Set Height 600
Set Padding 15
Set Theme "Catppuccin Mocha"
Set Framerate 24
Set TypingSpeed 50ms

Hide
Type "cd src/narrata/tests/assets && clear"
Enter
Sleep 1s
Show

Type "head -5 AAPL.csv"
Enter
Sleep 2s

Enter
Sleep 400ms

Type "uv run narrata AAPL.csv --ticker AAPL"
Enter
Sleep 3s

Enter
Sleep 400ms

Type "uv run narrata aapl_15m_5d.csv --ticker AAPL --currency '$'"
Enter
Sleep 3s

Enter
Sleep 400ms

Type "uv run narrata compare aapl_15m_1d.csv aapl_15m_5d.csv --ticker AAPL --currency '$'"
Enter
Sleep 3s

Sleep 2s
