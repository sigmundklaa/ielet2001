#include <WiFi.h>
#include <esp_now.h>

//MAC-address of ESP32 
//uint8_t broadcastAddress[] = {0xE8, 0x31, 0xCD, 0xE6, 0x0F, 0x20}; //ESP32 ESP-NOW gateway
uint8_t broadcastAddress[] = {0xE8, 0x31, 0xCD, 0xE5, 0x5A, 0x9C}; //ESP32 Sensornode

//Declare a esp_now object that holds info about other ESPs in the MESH/Peer-to-Peer network
esp_now_peer_info_t peerInfo;

//Callback function for when data is received from other ESP32
void OnDataRecv(const uint8_t * mac, const uint8_t *callbackData, int len) {
  //Write recieved data on serial UART
  Serial.write(callbackData, len);  
}
 
void setup() {
  //Start serial communication over Rx Tx UART
  Serial.begin(115200, SERIAL_8N1, 3, 1);
  
  // Set device as a Wi-Fi Station
  WiFi.mode(WIFI_STA);

  // Init ESP-NOW
  if (esp_now_init() != ESP_OK) {
    //Serial.println("Error initializing ESP-NOW");
    return;
  }
  
  //Register peer (other ESP32)
  memcpy(peerInfo.peer_addr, broadcastAddress, 6);
  peerInfo.channel = 0;
  peerInfo.encrypt = false; //Encryption is disabled
  
  //Add peer (other ESP32)     
  if (esp_now_add_peer(&peerInfo) != ESP_OK){
    //Serial.println("Failed to add peer");
    return;
  }
  
  //Register other ESP32 for a callback function that will be called when data is received
  esp_now_register_recv_cb(OnDataRecv);
}
 
void loop() {
  delay(10);
}
