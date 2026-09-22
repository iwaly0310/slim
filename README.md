# 宏謙健康減重指南（slim.hongchienclinic.com.tw）

靜態衛教網站，由 `build.js` 從 `content/` 產生到 `docs/`，以 GitHub Pages 發佈。

- 新增文章：在 `content/articles/` 放一個 `.md`，開頭用 frontmatter（title、category、summary、date、phases、order）。
- 常見問題：編輯 `content/faq.md`，每題以 `## 問題` 開頭。
- 網站資訊、階段與分類：`content/site.json`。
- 產生網站：`node build.js`；本機預覽：`node serve.js` 後開 http://localhost:5173 。
- 推上 GitHub 的 `main` 分支後，GitHub Pages 會自動更新。
