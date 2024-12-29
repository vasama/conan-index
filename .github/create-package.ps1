#!/usr/bin/pwsh

param(
	[string]$PackageName,
	[string]$PackageVersion,

	# Required by the update-recipe step:
	[string]$PackagePath=$null,
	[string]$GitHubRepository=$null,
	[string]$GitHubReference=$null,

	[string]$Step=$null
)

function Invoke-NativeCommand($Command) {
	& $Command $Args

	if (!$?) {
		exit $LastExitCode
	}
}

$ProgressPreference = 'SilentlyContinue'

$RecipeDir = "./recipes/$PackageName"

if (!$Step -or $Step -eq 'update-recipe') {
	if (!($GitHubRepository -match '^([^/]+)/([^/]+)$')) {
		throw "Invalid GitHub repository: $GitHubRepository"
	}
	$GitHubRepositoryName = $Matches[2]

	if (!($GitHubReference -match '^([^/]+)/(.+)$')) {
		throw "Invalid Git reference: $GitHubReference"
	}
	$GitHubReferenceName = $Matches[2]

	$Conanfile = "$RecipeDir/conanfile.py"
	$Conandata = "$RecipeDir/conandata.yml"

	if (Test-Path -PathType Leaf $Conanfile) {
		$Header = Get-Content -Path $Conanfile -TotalCount 1
		if (!($Header -match '^# VSM-CONANFILE-(\d+)\.(\d+)\.(\d+)$')) {
			throw 'The incompatible existing recipe may not be overwritten.'
		}
	}

	$SourceUrl = "https://github.com/$GitHubRepository/archive/refs/$GitHubReference.zip"

	$TemporaryDir = [System.IO.Path]::GetTempPath()
	$TemporaryDir = "$TemporaryDir/$((New-Guid).ToString("N"))"
	New-Item -Path $TemporaryDir -ItemType Directory | Out-Null

	try
	{
		$SourceDir = "$TemporaryDir/$GitHubRepositoryName-$GitHubReferenceName"
		$SourceZip = "$SourceDir.zip"

		# Download and expand source archive:
		Invoke-WebRequest $SourceUrl -OutFile $SourceZip | Out-Null
		$SourceHash = (Get-FileHash -Algorithm SHA256 $SourceZip).Hash.ToLowerInvariant()
		Expand-Archive -Path $SourceZip -DestinationPath $TemporaryDir

		# Copy the latest conanfile.py to the recipe directory:
		New-Item -Path $RecipeDir -ItemType Directory -ErrorAction Silent
		Copy-Item -Path "$PSScriptRoot/packaging/conanfile.py" -Destination $Conanfile

		# Update recipe conandata.yml:
		Invoke-NativeCommand python3 "$PSScriptRoot/update-conandata.py" `
			--root $SourceDir `
			--path $PackagePath `
			--name $PackageName `
			--version $PackageVersion `
			--src-url $SourceUrl `
			--src-hash $sourceHash `
			$Conandata
	}
	finally
	{
		Remove-Item -Path $TemporaryDir -Recurse -Force
	}
}

if (!$Step -or $Step -eq 'create-package') {
	Invoke-NativeCommand conan create $RecipeDir --version $PackageVersion
}

if (!$Step -or $Step -eq 'create-commit') {
	Invoke-NativeCommand git add $RecipeDir
	Invoke-NativeCommand git commit `
		--message "Add $PackageName/$PackageVersion" `
		--message "This commit was created by an automated process."
}
