import boto3
from PIL import Image, ImageOps
import json
import io

aws_rekognition_client=boto3.client('rekognition')

#This function request sends an image to Rekognition to detect faces in the image stored in S3
#Function returns a JSON object containing details about detected faces.
def detect_faces_from_image(bucketName, sourceImage):
        response = aws_rekognition_client.detect_faces(Image={'S3Object':{'Bucket': bucketName,'Name': sourceImage,},},)
        return response['FaceDetails']


#This function creates cropped images from an image with multiple faces based on detected faces returned by Rekognition
#It returns a list of names of those cropped images
def create_cropped_images_of_detected_faces(detected_faces,sourceImage, size_of_border, image_format):
        img = Image.open(sourceImage)
        count_of_cropped_faces =0
        list_of_cropped_images=[]
        actual_image_width, actual_image_height = img.size
        for face in detected_faces:
                x = int(face['BoundingBox']['Left']*actual_image_width)
                y = int(face['BoundingBox']['Height']*actual_image_height)
                width = int(face['BoundingBox']['Width']*actual_image_width)
                height = int(face['BoundingBox']['Top']*actual_image_height)
                crop_rectangle = ( x, y, width+x, height+y )
                cropped_im = ImageOps.expand(img.crop(crop_rectangle), border=size_of_border)
                name_of_cropped_image = "detected_face_" + str(count_of_cropped_faces) + ".jpg"
                cropped_im.save(name_of_cropped_image, image_format)
                list_of_cropped_images.append(name_of_cropped_image)
                count_of_cropped_faces = count_of_cropped_faces+1
        return list_of_cropped_images

#Performs search of images using images in S3 against a collection of images
#it returns a list of matched faces or and empty one if no much was found
def search_rekognition_for_matching_faces(list_of_faces_to_search_for, collectionId, bucketName, face_match_threshold, maximum_faces):
    for face_image_name in list_of_faces_to_search_for:
        print("First image name is: -- " + face_image_name)
        response=aws_rekognition_client.search_faces_by_image(CollectionId=collectionId,
                                Image={'S3Object':{'Bucket':bucketName,'Name':face_image_name}},
                                FaceMatchThreshold=face_match_threshold,
                                MaxFaces=maximum_faces)
                               
    print_search_results(response['FaceMatches'], face_image_name)

#Performs search of images using images on local drive against a collection of images
def search_rekognition_for_matching_faces(list_of_faces_to_search_for, collectionId, face_match_threshold, maximum_faces, image_format):
    for face_image_name in list_of_faces_to_search_for:
        open_image = Image.open(face_image_name)
        stream = io.BytesIO()
        open_image.save(stream,format=image_format)
        image_binary = stream.getvalue()

        response = aws_rekognition_client.search_faces_by_image(CollectionId=collectionId,Image={'Bytes':image_binary},FaceMatchThreshold=face_match_threshold, MaxFaces=maximum_faces)
        print_search_results(response['FaceMatches'], face_image_name)

#This function prints the results of from a SearchByImage API call
def print_search_results(matched_faces, face_image_name):
        print("#----------------------------------------------#")
        if matched_faces:
                print ('MATCH FOUND for ' + face_image_name + ', with ATTRIBUTES: ' )
                for match in matched_faces:
                        print ('FaceId: ' + match['Face']['FaceId'])
                        print ('Confidence: '+ str(match['Face']['Confidence']))
                        print ('Similarity: ' + "{:.2f}".format(match['Similarity']) + "%")
                        print("#----------------------------------------------#")
                        print("")
        else:
                
                print(" NO MATCH FOUND for " + face_image_name)
                print("#----------------------------------------------#")
                print("")

                
#This is the part that actually runs the functions to achieve the desired result
if __name__ == "__main__":

    #Declare and initialize variables
    collection_id='XXXXXXXXXXXX' # Collection you wish to search through
    bucket_name='XXXXXXXXXX' #S3 Bucket name
    test_file_name='XXXXXXXXXXXX' #name of image/url to image
    face_threshold_value = 80 # set percemtage o
    max_number_of_faces= 2 # limit number of matched faces returned
    size_of_border = 50 #Size of border around cropped image
    image_format = "JPEG"

    #Detect and return faces, reads image from S3
    detected_faces = detect_faces_from_image(
            bucket_name,
            test_file_name
            )
    #Create cropped images and return list of there names, uses image in same location as script
    list_of_cropped_faces = create_cropped_images_of_detected_faces(
            detected_faces,
            test_file_name, 
            size_of_border,
            image_format
            )

    #Search for each face in your collection of faces 
    search_rekognition_for_matching_faces(
            list_of_cropped_faces,
            collection_id,
            face_threshold_value,
            max_number_of_faces, 
            image_format
            )
  


