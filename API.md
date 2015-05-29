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
