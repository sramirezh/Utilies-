# To Clone and keep updated 

1. Clone your fork:

git clone git@github.com:YOUR-USERNAME/YOUR-FORKED-REPO.git

2. Add remote from original repository in your forked repository:

cd into/cloned/fork-repo
git remote add upstream git://github.com/ORIGINAL-DEV-USERNAME/REPO-YOU-FORKED-FROM.git #This defines the Upstream project
git fetch upstream

3. Updating your fork from original repo to keep up with their changes:

git pull upstream master

and then I have to push the changes that I got from the Upstream to the fork with:

git push origin master 

To check what is the origin and what is the fork, use 

git remote -v


https://help.github.com/articles/fork-a-repo/

# To pull and push to/from

git pull origin master



# To remove large files, GitHub suggests:

$ git rm --cached giant_file  Stage our giant file for removal, but leave it on disk

git commit --amend -CHEAD
Amend the previous commit with your change Simply making a new commit wont work, as you need to remove the file from the unpushed history as well

git push Push our rewritten, smaller commit


# Remove all local changes from your working copy, simply stash them:

git stash save --keep-index

If you dont need them anymore, you now can drop that stash:

git stash drop

# Change from SSH to HTTP 

git remote -v to check what is the current URL
git remote set-url origin URL, to set the new URL


# new repo from an existing project
git init.
Type git add to add all of the relevant files.
You’ll probably want to create a .gitignore file right away, to indicate all of the files you don’t want to track. Use git add .gitignore, too.
Type git commit


# Finding how many lines of code are in a project

git ls-files | grep "\.sh$" | xargs wc -l   this is for bash files



