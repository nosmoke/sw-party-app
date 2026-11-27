# אפליקציית החבורה

אפליקציית עזר לחבורת חרבות וכשפים: דפי דמות, חנות ציוד, ספר הרפתקה, מעקב הרפתקה ומפת מבוך.
האתר: https://nosmoke.github.io/sw-party-app/

## מבנה המאגר

| מה | איפה |
|---|---|
| קוד המקור של האפליקציה | `src/app.html` |
| סקריפט הבנייה | `tools/build.sh` |
| חיבור ל־Firebase (לגרסה החיצונית) | `tools/ext-head.html`, `ext.js`, `config.js` |
| חוקי האבטחה של Firestore | `firestore.rules` (מדביקים ב־Firebase ← Firestore ← Rules) |
| קבצים שהאפליקציה טוענת | `adventures/`, `items/`, `spells/` ועוד |
| האתר הבנוי | `index.html` (נבנה מ־`src/app.html`) |
| תיוג גרסאות אוטומטי | `.github/workflows/tag-version.yml` |

## בנייה

```
./tools/build.sh
```

הסקריפט בונה שתי גרסאות מאותו קוד:

- `index.html` — האתר החיצוני (GitHub Pages + Firebase).
- `dist-claude/index.html` — הגרסה שמתפרסמת כ־artifact ב־Claude, עם השמירה של Claude. התיקייה לא נשמרת במאגר.

שתי הגרסאות משתמשות באותם קבצים שליד `index.html`.

## גרסאות

עדכון שההודעה שלו מתחילה ב־`Version X.Y` יוצר לבד את התגית `vX.Y` ואת ה־Release, עם הערת הגרסה מתוך `RELEASES` שבקוד.
