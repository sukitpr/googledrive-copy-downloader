# secondary TODO : extract link from bluemedia (igg-games)   (extract hyperlink from hypertext)

# todo check if credentials is in the right folder(separate google auth and main)

"""
Documentation :
explain what this program does
explain client secret(how to replace it if needed) : https://developers.google.com/drive/api/v3/quickstart/python
directory : explain
download : the ile is chucked with pieces of ~100MB, need to download at least this amount beore appearing on screen
"""
import re

from googleapiclient.http import MediaIoBaseDownload


# get download folder from user :
# https://stackoverflow.com/questions/35851281/python-finding-the-users-downloads-folder


def get_Gdrive_folder_id(drive, driveService, name):  # return ID of folder, create it if missing
    body = {'title': name,
            'mimeType': "application/vnd.google-apps.folder"
            }
    query = "title='Temp folder for script' and mimeType='application/vnd.google-apps.folder'" \
            " and 'root' in parents and trashed=false"
    listFolders = drive.ListFile({'q': query})
    for subList in listFolders:
        if subList == []:  # if folder doesn't exist, create it
            folder = driveService.files().insert(body=body).execute()
            break
        else:
            folder = subList[0]  # if one folder with the correct name exist, pick it

    return folder['id']


def extract_file_ids_from_folder(drive, folderID):
    files = drive.ListFile({'q': "'" + folderID + "' in parents"}).GetList()
    fileIDs = []
    for file in files :
        fileIDs.append(file['id'])
    return fileIDs


def extract_files_id(links, drive):
    # copy of google drive file from google drive link :
    links = re.findall(r"\b(?:https?:\/\/)?(?:drive\.google\.com[-_?=a-zA-Z\/\d]+)",
                       links)  # extract google drive links
    try:
        fileIDs = [re.search(r"(?<=/d/|id=|rs/).+?(?=/|$)", link)[0] for link in links]  # extract the fileIDs
        for fileID in fileIDs:
            if drive.auth.service.files().get(fileId=fileID).execute()['mimeType'] == "application/vnd.google-apps.folder":
                fileIDs.extend(extract_file_ids_from_folder(drive, fileID))
                fileIDs.remove(fileID)
        return fileIDs
    except Exception as error:
        print("error : " + str(error))
        print("Link is probably invalid")
        print(links)


def copy_file(drive, id):
    fileOriginMetaData = drive.auth.service.files().get(fileId=id).execute()
    """remove 4 last characters of the original file name 
    and add file extension(should be .rar) in case the file extension is missing from the name """
    newFileName = fileOriginMetaData['originalFilename'][:-4] + "." + fileOriginMetaData['fileExtension']
    print("name of the file on your google drive and on the disk: " + newFileName)
    folderID = get_Gdrive_folder_id(drive, drive.auth.service, "Temp folder for script")
    copiedFileMetaData = {"parents": [{"id": str(folderID)}], 'title': newFileName}  # ID of destination folder
    copiedFile = drive.auth.service.files().copy(
        fileId=id,
        body=copiedFileMetaData
    ).execute()
    return copiedFile


def download_file(drive, file, destFolder):
    copiedFileMedia = drive.auth.service.files().get_media(fileId=file['id'])
    newFileName = file['title']
    file = open(destFolder + "\\" + newFileName, "wb+")
    downloader = MediaIoBaseDownload(file, copiedFileMedia, chunksize=104857600)  # change chunksize here
    done = False
    print("download in progress...")
    while done is False:
        status, done = downloader.next_chunk()
        print("\rDownload %d%%" % int(status.progress() * 100), end="")
    file.close()
    print("\ndownload completed : " + newFileName)


def delete_file(drive, id):
    drive.auth.service.files().delete(fileId=id).execute()
