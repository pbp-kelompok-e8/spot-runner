
<img width="1440" height="587" alt="banner_PBP_spotrunner" src="https://github.com/user-attachments/assets/47c4894c-102c-441c-9ab5-1175d1f06dac" />

## About Spot Runner
`SpotRunner` adalah platform digital yang menghubungkan para pecinta lari dengan berbagai event marathon di seluruh Indonesia. Kami hadir untuk mempermudah menemukan, mengikuti, dan bahkan menyelenggarakan event lari dengan cara yang praktis dan menyenangkan. Melalui SpotRunner, user dapat menjelajahi kumpulan event marathon yang lengkap. Dengan fitur filter, user dapat mencari event berdasarkan lokasi terdekat, tanggal pelaksanaan, dan tipe marathon seperti Fun Run, 10K, Half Marathon, hingga Full Marathon. Semua dirancang agar user dapat menemukan event yang paling sesuai dengan tujuan dan kemampuannya.

Sebagai seorang `runner`, kamu bisa mendaftar dan booking event dengan mudah hingga mengikuti event pilihanmu tanpa repot. Kamu juga akan mendapat koin setelah menyelesaikan suatu event dan dapat ditukar dengan merchandise jika koin mencukupi.

Sementara itu, bagi `event organizer`, SpotRunner menyediakan sistem manajemen event yang lengkap. Event organizer dapat membuat, mengelola, dan memantau event secara efisien — mulai dari pendaftaran peserta, pengaturan kategori lomba, hingga penyelenggaraan selesai.
Kami percaya bahwa lari bukan hanya tentang kecepatan, tapi juga tentang perjalanan dan kenyamanan. Dengan SpotRunner, kami ingin membangun ekosistem yang menyatukan pelari dan penyelenggara event dalam satu wadah yang profesional, transparan, dan mudah diakses.

## Our Features
Spot Runner memiliki fitur utama, diantaranya:
<details>
<summary>  Explore Marathon Event </summary>
Fitur Explore Marathon Event menampilkan kumpulan event marathon dari berbagai daerah dan kategori. Sistem dilengkapi dengan fitur filter yang memungkinkan penyaringan event berdasarkan lokasi, tipe marathon (Fun Run, 10K, Half Marathon, Full Marathon, dll), tanggal pelaksanaan, dan penyelenggara. Tujuan fitur ini adalah memudahkan pengguna dalam menemukan event yang relevan dan sesuai preferensi.
</details>
  
<details>
<summary>  Join Marathon Event </summary>
Fitur Join Marathon Event berfungsi untuk melakukan pendaftaran atau booking ke event marathon yang tersedia. Setiap pengguna yang berhasil mendaftar akan menerima tiket digital berisi detail event seperti nama event, lokasi, tanggal, dan participant ID. Setelah event selesai, sistem akan memberikan coin reward kepada peserta yang dapat dikumpulkan dan ditukarkan dengan merchandise yang tersedia.
</details>

<details>
<summary>  Review </summary>
Fitur Review memungkinkan pengguna memberikan penilaian terhadap event yang telah mereka ikuti. Review berupa komentar dan rating bintang ini akan ditampilkan secara publik pada halaman event, sehingga dapat berfungsi sebagai indikator kualitas bagi calon peserta lainnya. Bagi event organizer, fitur ini membantu meningkatkan kredibilitas serta memberikan masukan untuk pengembangan event berikutnya.
</details>

<details>
<summary>  Create & Manage Event (Event Organizer) </summary>
Fitur Create & Manage Event ditujukan untuk peran Event Organizer. Melalui fitur ini, organizer dapat membuat, memperbarui, dan menghapus event marathon secara mandiri. Fitur ini mencakup pengaturan detail event seperti nama, deskripsi, kategori, lokasi, dan tanggal pelaksanaan. Selain itu, event organizer juga dapat menambahkan merchandise yang akan menjadi hadiah penukaran bagi peserta berdasarkan coin yang mereka kumpulkan.
</details>

<details>
<summary>  Merchandise & Rewards </summary>
Fitur Merchandise & Rewards menjadi sistem penghargaan bagi pengguna yang aktif berpartisipasi dalam event. Coin yang diperoleh dari penyelesaian event dapat digunakan untuk menukar berbagai jenis merchandise, seperti perlengkapan lari, pakaian, atau hadiah eksklusif lainnya. Fitur ini berfungsi untuk meningkatkan engagement pengguna serta memberikan insentif bagi partisipasi berkelanjutan dalam platform.
</details>

## Nama Anggota Kelompok
- Peter Yap (2406432910)
- Kadek Chandra Rasmi (2406426473)
- Emir Fadhil Basuki (2406421440) 
- Muhammad Qowiy Shabir  (2406435982) 
- William Jonnatan (2406429020)

## Daftar Modul
| No |    Nama Modul   |                                               Deskripsi                                                                               | Anggota |  
| -- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ------- | 
| 1  | User            | Autentikasi user, profile user, CRUD review, tukar poin, booking event.                                                               |  Peter  | 
| 2  | Event           | Event model + public listing & detail. Menyimpan data event, CRUD untuk organizer (Create/Update/Delete), halaman list/detail publik. | William | 
| 3  | Merchandise     | CRUD Merchandise dan handle penukaran merch.                                                                                          | Chandra | 
| 4  | Review          | Reviews & ratings. Menyimpan review event, menampilkan rata-rata, menampilkan semua review untuk organizer.                           |  Qowiy  | 
| 5  | Event Organizer | Organizer tools. Untuk melihat upcoming events, participant counts, recent reviews, list participants per event, CRUD Merchandise.    |   Emir  | 

## Sumber Dataset
  1. https://jakartarunningfestival.id/
  2. https://lariku.info/
  3. https://uiultra.com/
  4. https://kalenderlari.com/jadwal/
  5. https://jadwallari.id/

## Jenis Pengguna
#### 1. Runner 
Akun pengguna biasa. Memiliki atribut:
- Username 
- Password
- Email
- Base location
- Poin

Akun runner juga memiliki relasi dengan:
- Review (one to many) 
- Event (many to many)

Pengguna dengan role ini dapat mengakses fitur lihat event, booking event, review event yang sudah dilakukan, menukar poin dengan barang merch, dan melihat history event

#### 2. Event organizer
Merupakan pengguna yang dapat membuat dan mengatur event. Pengguna ini memiliki atribut:
- Username
- Password
- Profile Picture
- Base Location

Akun event organizer memiliki relasi dengan:
- Event (one to many)
- Review (one to many)
- Merchandise (one to many)

Pengguna ini dapat menambahkan event-event baru atau pun mengubah detail-detail pada event yang telah dibuat oleh pengguna sebelumnya. Selain itu, pengguna dengan role ini juga dapat membatalkan atau menghapus event-event yang tidak diinginkan. Pengguna ini juga memiliki akses untuk melihat event yang sedang berjalan, sudah selesai, ataupun dibatalkan. 

### URL Deployment PWS : 
https://william-jonnatan-spotrunner.pbp.cs.ui.ac.id/

### Design File Figma:
https://www.figma.com/design/bPYWoCrt7XljkLbyVaHgRU/PBP-Kelompok?node-id=0-1&t=6whKcuuazAz6Wb6q-1
