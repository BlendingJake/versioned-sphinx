from versioned_sphinx.git import Git

a = Git("../JARCH-Vis")

original = a.get_current_branch()
print(f"Original branch: {original}")

branches = a.get_branches()
print(f"Got {len(branches)} branches")

not_main = [b for b in branches if "master" not in b.branch]
a.checkout_branch(not_main[0])
print(f"Now in branch: {a.get_current_branch()}")

tags = a.get_tags()
print(f"Got {len(tags)} tags")

a.checkout_tag(tags[0])
print(f"Now in branch: {a.get_current_branch()}")

a.checkout_branch("master")
