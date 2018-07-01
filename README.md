
## B2 Backblaze Cloud Total Storage Usage / Simple B2 Module-Lib Class


### What it does:

B2 CLI ( https://www.backblaze.com/b2/docs/quick_command_line.html ) doesnt currently support 
obtaining total b2 cloud storage usage (all buckets) - this fills the gap for me nicely.

I use B2 for personal (free) storage utilizing the 10GB free tier.  This prevents having to 
visit the web interface to get total storage / caps.

(Uses my personal B2 library/module BackBlazeB2 - which leverages B2 API)

### Usage:

```
get-b2storageusage <accountId> <applicationKey>
```

### Returns:

```
Current BackBlaze B2 Buckets for account:
-----
somebucket [size: 0 (0 B)]
somebucket2 [size: 3381087633 (3.15 GB)]
-----
Total size [3.15 GB]
```

### Extended Note
Uses BackBlazeB2 module (included) - personal B2 library/module BackBlazeB2 (which leverages B2 API).  Wanted to play around
with writing a simple module/lib.  Amateur hour at this point since it is for my personal usage.  WIP!

### Thanks 
BackBlaze B2 API : https://www.backblaze.com/b2/docs/