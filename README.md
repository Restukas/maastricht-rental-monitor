# Maastricht Rental Monitor

Automatinis Mastrichto nuomos skelbimų stebėjimas – veikia GitHub Actions (nemokama).

## Kaip paleisti

### 1. Sukurti GitHub repozitorijų

```bash
cd maastricht-rental-monitor
git init
git add .
git commit -m "init"
gh repo create maastricht-rental-monitor --public --push --source=.
```

### 2. Pridėti pranešimų nustatymus (GitHub Secrets)

Eiti į: `GitHub repo → Settings → Secrets and variables → Actions → New repository secret`

#### Discord (rekomenduojama)
1. Discord → savo serveris → kanalas → Edit Channel → Integrations → Webhooks → New Webhook → Copy URL
2. Secrets: `DISCORD_WEBHOOK` = `https://discord.com/api/webhooks/...`

#### Gmail (alternatyva)
1. Google Account → Security → 2-Step Verification → App passwords → sukurti "Mail"
2. Secrets:
   - `GMAIL_USER` = `ernestas.nelkinas@gmail.com`
   - `GMAIL_APP_PASSWORD` = (16 simbolių slaptažodis)

### 3. Paleisti rankiniu būdu (testavimui)

GitHub repo → Actions → "Maastricht Rental Monitor" → Run workflow

### 4. Automatinis paleidimas

GitHub Actions paleidžia skriptą **kas 30 minučių** automatiškai.

## Stebimos svetainės

| Kodas | Svetainė |
|---|---|
| maasland | maaslandrelocation.nl |
| vbt | vbtverhuurmakelaars.nl |
| housing4you | housing4you.eu |
| househunting | househunting.nl |
| hypodomus | hypodomus-maastricht.nl |
| huizenbeheer | huizenbeheermaastricht.nl |
| kamermaastricht | kamermaastricht.com |
| prohousing | pro-housingrooms.nl |
| roofz | roofz.eu |
| woonpleinlimburg | woonpleinlimburg.nl |

## Platformos su įmontuotais pranešimais (rankinis nustatymas)

Šias platformas nustatykite tiesiogiai jų svetainėse:

- [Funda](https://www.funda.nl) – sukurti paiešką + el. pašto pranešimai
- [Pararius](https://www.pararius.com/apartments/maastricht) – „Maak een zoekopdracht"
- [Kamernet](https://kamernet.nl/en/for-rent/student-housing-maastricht) – „Zoekopdracht aanmaken"
- [Huure.nl](https://huure.nl) – paskyros pranešimai
- [HousingAnywhere](https://housinganywhere.com/s/Maastricht--Netherlands/student-accommodation)
- [Huisly](https://huisly.nl) – **NEMOKAMA programėlė, stebi 1400+ šaltinių**
