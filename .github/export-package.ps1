#!/usr/bin/pwsh

param(
	[string]$PackageName,
	[string]$PackageVersion,
	[string]$PackageUser=$null,
	[string]$PackageChannel=$null,

	[string]$Remote,
	[switch]$Binary=$false,

	[string]$Step=$null
)

function Invoke-NativeCommand($Command) {
	& $Command $Args

	if (!$?) {
		exit $LastExitCode
	}
}

$RecipeDir = "./recipes/$PackageName"

if (!$Step -or $Step -eq 'conan-export') {
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

	$ConanArgs = New-Object System.Collections.Generic.List[System.Object]

	if (!$Binary) {
		$ConanArgs.Add('--only-recipe')
	}

	Invoke-NativeCommand conan upload --remote $Remote --check @ConanArgs $Reference
}
