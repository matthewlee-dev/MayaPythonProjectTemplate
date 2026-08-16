# Project layout

```
my-cool-tool/
├── src/my_cool_tool/     ← your code goes here
├── tests/                ← your tests go here
├── docs/                 ← your docs go here
├── scripts/              ← builds the Maya module
├── .github/workflows/    ← the automatic checks
├── pyproject.toml        ← project settings and dependencies
├── release.py            ← cuts a release
├── README.md
└── CONTRIBUTING.md
```

Your code folder is named after your repo, and that name is what you import:
`import my_cool_tool`.
