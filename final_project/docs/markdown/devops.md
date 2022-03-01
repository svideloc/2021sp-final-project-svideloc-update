# Devops

Due to company standards I used similar but different tools for my builds, publishing libraries and such. I won't commit these files to my repo as they have many internal references, but this was one of my biggest takeaways from this course so I wanted to share what I did here. I had no prior experience taking on the more dev-ops type tasks prior to this class.

## Jenkins
Jenkins is a free opensource CI/CD tool. The Jenkins build lints/tests code but also publishes the pypi repo to nexus and builds a docker image with semantic versioning.

## Gitlab Runners
Gitlab runners enable us to lint and test code that is pushed up to developer branches without building and publishing a new version of the code.

## Nexus
As with many companies are repositories are private, and nexus allows us the flexibility to publish our repos so they can be accessible to anyone with the proper permissions/certs.
