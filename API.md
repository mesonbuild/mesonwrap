# The API
To make an API call, make a request to URL corresponding to given call (URLs are listed below). Parameters are denoted by angle brackets. Result is represented as JSON map with `"output": "ok"` key-value pair on success or `"output": "notok"` on failure or response with content and mime-type. The rest of the map represents result of the call and is described below for individual calls.

# URL

## List all projects
`/projects`
```JSON
{
  "output": "ok",
  "projects": [
    {
      "name": "zlib",
      "versions": [
        {
          "branch": "1.2.8",
          "revision": 1
        }
      ]
    }
  ]
}
```

## Getting info about project
`/projects/<project>`
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
`/projects/<project>/get_wrap?branch="<branch>"&revision="<revision>"`

Will return `.wrap` file. `revision` and `branch` are mandatory.

## Getting zip
`/projects/<project>/get_zip?branch="<branch>"&revision="<revision>"`

Will return zip file with all needed content for meson. `revision` and `branch` are mandatory.
