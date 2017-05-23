#Reload configuration file

This can be done either from within tmux, by pressing Ctrl+B and then : to bring up a command prompt, and typing:

:source-file ~/.tmux.conf

Or simply from a shell:

$ tmux source-file ~/.tmux.conf


Taken from https://gist.github.com/henrik/1967800
###tmux cheatsheet

As configured in my dotfiles.

start new:

tmux

start new with session name:

tmux new -s myname

attach:

tmux a  #  (or at, or attach)

attach to named:

tmux a -t myname

list sessions:

tmux ls

kill session:

tmux kill-session -t myname

In tmux, hit the prefix ctrl+b and then:
Sessions

:new<CR>  new session
s  list sessions
$  name session

Windows (tabs)

c           new window
,           name window
w           list windows
f           find window
&           kill window
.           move window - prompted for a new number
:movew<CR>  move window to the next unused number

Panes (splits)

%  horizontal split
"  vertical split

o  swap panes
q  show pane numbers
x  kill pane
⍽  space - toggle between layouts

Window/pane surgery

:joinp -s :2<CR>  move window 2 into a new pane in the current window
:joinp -t :1<CR>  move the current pane into a new pane in window 1

    Move window to pane
    How to reorder windows

Misc

d  detach
t  big clock
?  list shortcuts
:  prompt

Resources:

    cheat sheet

Notes:

    You can cmd+click URLs to open in iTerm.

TODO:

    Conf copy mode to use system clipboard. See PragProg book.
