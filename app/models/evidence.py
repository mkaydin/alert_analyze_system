from pydantic import BaseModel


class ImageFile(BaseModel):
    fileName: str = ""
    filePath: str = ""
    filePublisher: str | None = None
    fileSize: int | None = None
    sha1: str | None = None
    sha256: str | None = None


class UserAccount(BaseModel):
    accountName: str | None = None
    domainName: str | None = None
    userSid: str | None = None


class DeviceEvidence(BaseModel):
    hostName: str = ""
    osPlatform: str = ""
    osBuild: int | None = None
    version: str = ""
    riskScore: str = ""
    verdict: str = ""
    lastIpAddress: str = ""
    lastExternalIpAddress: str = ""
    deviceDnsName: str = ""
    loggedOnUsers: list[UserAccount] = []


class ProcessEvidence(BaseModel):
    processName: str = ""
    processCommandLine: str = ""
    processId: int | None = None
    parentProcessId: int | None = None
    userAccount: UserAccount | None = None
    verdict: str = ""
    imageFile: ImageFile | None = None
