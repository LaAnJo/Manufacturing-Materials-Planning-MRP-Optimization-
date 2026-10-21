# Upload the project to a NEW GitHub repository using VS Code (PowerShell)

This project should be a separate GitHub repository rather than embedded inside an unrelated procurement or demand forecasting project.

1. Extract the downloaded project ZIP into `Documents\GitHub-Projects\Manufacturing_Materials_MRP_Optimization`.
2. On github.com/LaAnJo, create an EMPTY repository called `Manufacturing-Materials-MRP-Optimization` (do not initialize with a GitHub README).
3. Open the project root folder in VS Code (not the parent folder).
4. Review source data attribution, `.gitignore`, generated `.sqlite`, and HTML assets before publishing.

```powershell
git init -b main
git config user.name "LaAnJo"
git config user.email "62889201+LaAnJo@users.noreply.github.com"
git status
git add .
git diff --cached --stat
git commit -m "feat: build concrete material requirements planning simulation"
git remote add origin https://github.com/LaAnJo/Manufacturing-Materials-MRP-Optimization.git
git push -u origin main
```

For future revisions, `git status` → review diff → stage targeted changes → commit → push. If the new GitHub repository is NOT empty, clone it first and copy the project contents into that clone rather than initializing a divergent history.
