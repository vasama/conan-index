#!/usr/bin/pwsh

param(
	[string]$Remote,

	[string]$PackageName,
	[string]$PackageVersion,
	[string]$PackageUser=$null,
	[string]$PackageChannel=$null,

	[string]$Step=$null
)

function Invoke-NativeCommand($Command) {
	& $Command $Args
	if (!$?) { exit 1 }
}

if (!$Step -or $Step -eq 'conan-export') {
	$RecipeDir = Invoke-NativeCommand python3 "$PSScriptRoot/get-recipe-directory.py" `
		--root . `
		--name $PackageName `
		--version $PackageVersion

	$ConanArgs = New-Object System.Collections.Generic.List[System.Object]

	if ($PackageUser) {
		$ConanArgs.Add('--user')
		$ConanArgs.Add($PackageUser)
	}

	if ($PackageChannel) {
		$ConanArgs.Add('--channel')
		$ConanArgs.Add($PackageChannel)
	}

	Invoke-NativeCommand conan export --version $PackageVersion @ConanArgs $RecipeDir
}

if (!$Step -or $Step -eq 'conan-upload') {
	$Reference = "$PackageName/$PackageVersion"

	if ($PackageUser) {
		$Reference = "$Reference@$PackageUser"
		if ($PackageChannel) {
			$Reference = "$Reference/$PackageChannel"
		}
	}

	Invoke-NativeCommand conan upload --remote $Remote --check $Reference
}
