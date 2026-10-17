# Dataset source and provenance assessment

## Identified upstream file

The local workbook has the same filename as the workbook listed in the public `Data/` directory of [Neeraj08823/Sugar_cosmetics_Instagram_Analytics](https://github.com/Neeraj08823/Sugar_cosmetics_Instagram_Analytics/tree/main/Data). Its repository README describes a 50K+ row Sugar Cosmetics Instagram analytics dataset covering April 2024–April 2025 and reports rounded aggregate values for reach, impressions, engagements, and engagement rate.

The local workbook and CSV contain 50,000 rows over the same date range. Recomputed from the local CSV:

| Measure | Local calculation | Upstream README claim |
|---|---:|---:|
| Summed reach | 987,423,288 | 987M |
| Impressions | 1,276,045,750 | 1B |
| Likes + comments + shares + saves | 183,164,417 | 183M engagements |
| Weighted engagement rate | 18.5497% | 18.55% |

The matching filename, date span, and rounded aggregates strongly support that the local files came from that public project. The [upstream project README](https://github.com/Neeraj08823/Sugar_cosmetics_Instagram_Analytics) is the available source attribution. The exact remote workbook bytes were not independently fetched and compared with the local SHA-256.

## What this establishes and what it does not

It establishes a likely public-project source for this dataset. It does **not** establish that the records were collected from Sugar Cosmetics' official Instagram account, that the values came from Instagram or Meta Insights, that one row is one unique post, or that the sample is representative. The upstream documentation does not give a collection method, account ID, API/export evidence, row-level post IDs, or sampling procedure. The near-even content and campaign counts and 136.612 records per calendar day should be treated as sampling/row-grain warnings.

The upstream README mentions an MIT license for its project, but the dataset's ownership and license scope have not been independently confirmed. Check the upstream license and obtain permission before redistributing the workbook or presenting its values as official brand performance.

## Reporting rule

Describe results as **analysis of the dataset published with the upstream project**. Do not call them verified Sugar Cosmetics account performance. Use `reports/reproducibility_manifest.json` to identify the exact local bytes and preserve the source link alongside future extracts.
