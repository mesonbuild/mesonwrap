# The API
To make an API call, make a request to URL corresponding to given call (URLs are listed below). Parameters are denoted by angle brackets. Result is represented as JSON map with `"output": "ok"` key-value pair on success or `"output": "notok"` on failure or response with content and mime-type. The rest of the map represents result of the call and is described below for individual calls.

# URL

## List all projects
`/v1/projects`
```JSON
{
  "output": "ok",
  "projects": [
    "sqlite"
  ]
}
```

## Getting info about project
`/v1/projects/<project>`
```JSON
{
  "name": "zlib",
  "output": "ok",
  "metadata": {
    "homepage": "http://zlib.net",
    "description": "Wrap definitions for the zlib library"
  },
  "versions": [
    {
      "branch": "1.2.8",
      "revision": 1
    }
  ]
}
```

## Getting wrap file
`/v1/projects/<project>/<branch>/<revision>/get_wrap`

Will return `.wrap` file.

## Getting zip
`/v1/projects/<project>/<branch>/<revision>/get_zip`

Will return zip file with all needed content for meson.

## Querying the latest revision of the package
`/v1/query/get_latest/<project>`
```JSON
{
  "branch": "3.5.1",
  "output": "ok",
  "revision": 2
}
```

## Querying all projects that have prefix
`/v1/query/byname/<project_prefix>`
```JSON
{
  "output": "ok",
  "projects": [
    "protobuf",
    "protobuf-c"
  ]
}
```
