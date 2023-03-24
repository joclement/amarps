## v0.15.0 (2023-03-24)

### Feat

- Log input values for most conversion helpers
- Log url of profile download
- Log most catched exceptions as errors
- Make sleep time configurable
- Be able to split German-like formatted dates
- Print default option value

### Refactor

- Make mypy happy
- Improve function name
- Use more suitable parent exception

## v0.14.0 (2023-03-15)

### Feat

- Reduce currently hardcoded sleep time
- Allow user to login

### Refactor

- Reduce redundancy
- Pin down buggy behavior

## 0.13.1 (2023-03-08)

### Fix

- Fix adding changelog to package

## 0.13.0 (2023-03-08)

### Feat

- Validate input a bit more strictly
- Relax parsing global ratings

### Perf

- Only do needed number of splits/replacements

## v0.12.0 (2023-03-06)

### Feat

- Shorten package/application name
- Add logging
- Check if attribute exists
- Make it optional to get image
- Allow "," and "." in integer field
- Convert number of ratings to an integer
- Download profiles by default
- Be more tolerant regarding found helpful parsing

### Fix

- Fail when no format matches
- Drop duplicate short option

### Refactor

- Hide test data in other repo

### Perf

- Do max one split as only 1 is required

## v0.10.1 (2023-03-03)

### Fix

- Fix running the tool

## v0.10.0 (2023-03-03)

### Feat

- Be able to parse german dates
- Rename application
- Parse different date structure
- Allow using firefox as the browser
- Avoid month name in date output

### Fix

- Update page URL

### Refactor

- Shorten class name
- Make code more browser agnostic
- Drop duplicate include
- Avoid deprecation warning
- Have more specific type info

## v0.9.0 (2023-02-01)

### Feat

- Note when profile is not extracted
- Drop superfluous print statement
- Drop duplicate json field

## v0.8.0 (2023-01-31)

### Feat

- Extract whether there is a profile image
- Add a workaround for HTTP 503
- Store html also for failing HTTP status
- Allow setting a stop page
- Improve wording of option help text
- Continue when profile extraction fails

## v0.7.0 (2023-01-30)

### Feat

- Handle profile found helpful input
- Handle profile review date input
- Skip conversion for null values of certain fields
- Refine profile reviews like reviews
- Make conversion more tolerant
- Author is not needed
- Drop histogram for now
- Make conversion more strict (again)
- Turn found helpful into a number
- Store the rating of a review as an integer
- Show when certain exception occurs

### Fix

- Make rating extraction fail-safe again

## v0.6.0 (2023-01-21)

## v0.5.0 (2023-01-07)

## v0.4.0 (2023-01-06)

## v0.3.0 (2023-01-06)

## v0.2.0 (2023-01-01)

## v0.1.0 (2022-12-30)
