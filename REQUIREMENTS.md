# Purpose

A python photo tagging utility. With it's first priority on adding exif date information to PNG files. The utility should seek
to synchronize the files creation, modification and exif Date fields with each other as directed by the user's command invocation.

The second purpose of the utility shall be to show a given files exif Date related fields and it's UNIX modification date.

The third purpose of the utility is to synchronize the time information of a photo's time information with the "sync" CLI subcommand.
When this form of phototag is invoked, the utility will read the EXIF DateTime (preferred) or Date field and the file's modification time.
Use the oldest date time information found. Set all the date time fields that are out of agreement with this date time value. The sync subcommand
should be invokable with multiple files.

## Design

A modular project designed with independent classes for operating on format types (e.g. PNG, jpgs, etc)

Project requirements:
- use uv to maintain the code and its dependencies
- the src folder will contain the support modules and classes for the project
- A tests folder will contain any permanent unit tests written to maintain the integrity of the code to adhere to requirements.
- Use the python click module to parse command arguments.
- Provide a tqdm progress meter when processing many files.
- When processing multiple files, when finished display how many seconds it required with a files per second statistic or seconds per file stat as appropriate.

## feature requirements

### Date tagging

- given a date write exif Date information into the PNG file.
- change the unix file time attributes of the file to match the date specified (creation and modification times)

## Commands

Here is an example of expected command invocation

### "tag photo" command

#### Invocation

```
phototag --date="20251103" my-photo.png
```

#### Expectations

- my-photo.png will have the exif Date set with to 20251103
- my-photo.png modification, creation time set to 20251103

### "tag photo" with mod date command

### Invocation

Suppose my-photo.png has a date of May 1st 1971.

```
phototag --date="mod" my-photo.png
```

#### Expectations

- the date specified will be taken from the my-photo.png modification date at the time the program starts
- my-photo.png will have the exif Date set with to 19710501
- Also set the DateTime component to include the time portion of the modfication time
- Make sure the final png file's creation and modification time is set to it's original modification date time.

### "tag photos" with respective mod dates command

### Invocation

```
phototag --date="mod" *.png
```

#### Expectations

- Each file matched by the glob specification, will have there exif Date to their respective file modification date.
- Also set the DateTime component to include the time portion of the modification time
- Make sure the final png file's creation and modification time is set to it's original modification date time.

### "show photo tags" command

### Invocation

```
phototag show my-image.png
```

#### Expectations

- Nicely print the exif Date related fields of the image
- Nicely print the modification and creation dates of the file.

### "ls photo information" command

Provide a interface like the UNIX ls command. This command will give a quick overview of the date information set for the files.

#### Invocation

```
phototag ls *.png
```

#### Expectations

- Display in a nice columnar format the following information
  * path_to_image
  * file size in easy to read human readable units
  * exif.DateTime
  * exif.fs_modification_date
- Display the three fields formatted neatly in there own columns
- Order the list of photos by their exif.DateTime field value. Oldest file first
- If the set of options -ltr are passed to the ls command. Sort the files in reverse order. Oldest files last.
- Ignore the "-l" option as the default ls display is long format.
- Ignore the "-t" option as the files are by default sorted by time
- The "-r" option sorts the files in reverse order. E.g.: oldest files last.
