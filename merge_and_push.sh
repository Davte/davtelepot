#!/bin/bash

# Merge develop into master and push both branches; checkout to develop at the end.

git checkout master;
git merge develop;
git checkout develop;
git push origin master develop;
