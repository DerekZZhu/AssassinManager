# Manual Score Checker

This folder contains files for manually checking the accuracy of stats. As input, it takes a `kill_log.txt` file which is expected to contain a list of killer-victim pairs in order of assassination, such as the following:

```
Joshua_Jung	    Eric_Bae
Joshua_Jung	    Eric_Bae
Michael_Xu	    Nathan_Li
Janani_Raghavan Joshua_Jung
Karim_Maftoun   Derek_Zhu
...
```

Note that this format is what you get if you select the record cells from Google sheets and paste them into a `.txt` file.

The only dependency required to run this is `numpy`. The defined constants at the top of the file are game-specific and can be changed.
