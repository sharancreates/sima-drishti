# Stitch Screen Downloader for BorderVision Surveillance Project (ID: 448804983720992231)

$screens = @(
    @{
        Name = "1_BorderVision_Tactical_Splash_Screen"
        ScreenshotUrl = "https://lh3.googleusercontent.com/aida/AEtjO1XhMRYvpnJ3N5Z0vUoKqgS6VWZweVJg3GZCmyi2wpWH5aRCQIBIU74-CUQJOVQYi9KOmlx9y_GzhctI_KSWaJHYuOBVKUeBxIgmlg70THy1gYF_6XgyRJbYI7MHtFlVlXUrD0lhXzqn2yNYWcGzXFLME67DybH-cJMsKPME2gq9nce8dAnwHGV07bKPU69r9aci-z2JnQVa0XqAh11z9nm_G0-pDh28QmrD4QblMZSu_RuHV4ZCn8XLhw"
        HtmlUrl = "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ6Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpZCiVodG1sXzAwMDY1YWNhN2UwZTcyNDgwMWI0ZTg5ZTk5MGNiNzliEgsSBxCmr9mT4A4YAZIBIgoKcHJvamVjdF9pZBIUQhI0NDg4MDQ5ODM3MjA5OTIyMzE&filename=&opi=89354086"
    },
    @{
        Name = "2_BorderVision_Command_Center_Dashboard"
        ScreenshotUrl = "https://lh3.googleusercontent.com/aida/AEtjO1UK1bqu8ymJEsHHDLrNHWAbUd1o0WrBfHAfsb9mgqSjZtRnfmIaNG8D0VNtMCW0DoSeGyvY_YqDs6JQA4ayW53YiWy7U-xwEgYrxi9T6fgsSoT3iN8N-IZBjOlZ5RfpfNAOuY0ElOR-R50i2LTr-6XQazAkzMCdAukJjUFgdZ9YhM1x419oo46kQ_Y7ck4JRvP5kJ7f0Kzs8mHdtJyQdv1WkBEzxJupULunEdTefqXRtdYSkz0VOQnCMA"
        HtmlUrl = "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ6Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpZCiVodG1sXzAwMDY1YWNhODJmMjU0OTUwNzNhZmIxODY4MjE1OGM1EgsSBxCmr9mT4A4YAZIBIgoKcHJvamVjdF9pZBIUQhI0NDg4MDQ5ODM3MjA5OTIyMzE&filename=&opi=89354086"
    },
    @{
        Name = "3_BorderVision_Alert_Details_QRT_Dispatch_Modal"
        ScreenshotUrl = "https://lh3.googleusercontent.com/aida/AEtjO1UAiHCTD8ckkwjuLk80NjMR_2IKnJ2Nj3N1GrKG_xc2pCWeXaE6pkRLmCrvUbwyXbW74iIMNxgQYGL0Ewd0glPb-vqWdOhlAAEFEG6rnqHvkMbkjrh8zimaHBL3gTlsPslnfXqBHtUM5vJTtxMUg3Bvfx7bU7FZ5AAhp8QKfhn9-paZy7CnwOy5tFsgtLNWAE0Nd7dzqIdb4OJGtwiwQ8rRUp1HL03ODZSMUDy1dkkQB84RfVZjBDnGOA"
        HtmlUrl = "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ6Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpZCiVodG1sXzAwMDY1YWNhODVlYjQzYWMwMWE2MGIzZWY3MWIwNTk4EgsSBxCmr9mT4A4YAZIBIgoKcHJvamVjdF9pZBIUQhI0NDg4MDQ5ODM3MjA5OTIyMzE&filename=&opi=89354086"
    }
)

$targetDir = $PSScriptRoot
if (-not $targetDir) { $targetDir = "frontend" }

foreach ($s in $screens) {
    $imgFile = Join-Path $targetDir "$($s.Name).png"
    $htmlFile = Join-Path $targetDir "$($s.Name).html"

    Write-Host "Downloading $($s.Name) screenshot..."
    curl.exe -L "$($s.ScreenshotUrl)" -o "$imgFile"

    Write-Host "Downloading $($s.Name) html..."
    curl.exe -L "$($s.HtmlUrl)" -o "$htmlFile"
}

Write-Host "All downloads finished successfully!"
