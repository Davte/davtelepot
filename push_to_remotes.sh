#!/bin/bash

# Merge develop into master and push both branches; checkout to develop at the end.

git push origin main develop;
git push bitbucket main develop;
git push github main;
