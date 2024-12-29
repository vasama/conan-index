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
	if (!$?) { exit 1 }
}

$global:ProgressPreference = 'SilentlyContinue'

$RecipeDir = "./recipes/$PackageName/v1"

if (!$Step -or $Step -eq 'update-recipe') {
	if (!($GitHubRepository -match '^([^/]+)/([^/]+)$')) {
		throw "Invalid GitHub repository: $GitHubRepository"
	}
	$GitHubRepositoryName = $Matches[2]

	if (!($GitHubReference -match '^refs/(heads|tags)/(.+)$')) {
		throw "Invalid Git reference: $GitHubReference"
	}
	$GitHubReferenceName = $Matches[2] -replace '/','-'

	$Conanfile = "$RecipeDir/conanfile.py"
	$Conandata = "$RecipeDir/conandata.yml"

	if (Test-Path -PathType Leaf $Conanfile) {
		$Header = Get-Content -Path $Conanfile -TotalCount 1
		if (!($Header -match '^# VSM-CONANFILE-(\d+)\.(\d+)$')) {
			throw 'The incompatible existing recipe may not be overwritten.'
		}
	}

	$SourceUrl = "https://github.com/$GitHubRepository/archive/$GitHubReference.zip"
	"Source URL: $SourceUrl"

	$TemporaryDir = [System.IO.Path]::GetTempPath()
	$TemporaryDir = "$TemporaryDir/$((New-Guid).ToString("N"))"
	New-Item -Path $TemporaryDir -ItemType Directory | Out-Null

	try
	{
		$SourceDir = "$TemporaryDir/$GitHubRepositoryName-$GitHubReferenceName"
		$SourceZip = "$SourceDir.zip"

		# Download and expand source archive:
		Invoke-WebRequest $SourceUrl -OutFile $SourceZip | Out-Null
		Expand-Archive -Path $SourceZip -DestinationPath $TemporaryDir

		$SourceHash = (Get-FileHash -Algorithm SHA256 $SourceZip).Hash.ToLowerInvariant()
		"Source SHA256: $SourceHash"

		# Create the recipe directory:
		New-Item -Path $RecipeDir -ItemType Directory -ErrorAction Silent | Out-Null

		# Update recipe conandata.yml:
		Invoke-NativeCommand python3 "$PSScriptRoot/update-conandata.py" `
			--root $SourceDir `
			--path $PackagePath `
			--name $PackageName `
			--version $PackageVersion `
			--src-url $SourceUrl `
			--src-hash $SourceHash `
			$Conandata

		# Copy the latest conanfile.py to the recipe directory:
		Copy-Item -Path "$PSScriptRoot/packaging/conanfile.py" -Destination $Conanfile
	}
	finally
	{
		Remove-Item -Path $TemporaryDir -Recurse -Force
	}
}

if (!$Step -or $Step -eq 'create-package') {
	Invoke-NativeCommand conan create --version $PackageVersion --build missing $RecipeDir
}

if (!$Step -or $Step -eq 'create-commit') {
	Invoke-NativeCommand git add $RecipeDir
	Invoke-NativeCommand git commit `
		--message "Add $PackageName/$PackageVersion" `
		--message "This commit was created by an automated process."
}

if (!$Step -or $Step -eq 'push-changes') {
	Invoke-NativeCommand git push
}
