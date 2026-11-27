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
| קבצים שהאפליקציה טוענת | `items/`, `spells/` ועוד (ספרי ההרפתקה נמצאים בספרייה ב־Firebase, והמקורות במאגר הפרטי sw-party-books) |
| האתר הבנוי | `index.html` (נבנה מ־`src/app.html`) |
| תיוג גרסאות אוטומטי | `.github/workflows/tag-version.yml` |

## בנייה

```
./tools/build.sh
```

הסקריפט בונה את האתר (`index.html`, ל־GitHub Pages + Firebase) מתוך `src/app.html`, יחד עם הקבצים שלידו.

## גרסאות

עדכון שההודעה שלו מתחילה ב־`Version X.Y` יוצר לבד את התגית `vX.Y` ואת ה־Release, עם הערת הגרסה מתוך `RELEASES` שבקוד.
