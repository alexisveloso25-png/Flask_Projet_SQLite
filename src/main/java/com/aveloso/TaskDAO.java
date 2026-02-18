package com.aveloso;
import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class TaskDAO {
    private String url = "jdbc:mysql://mysql-aveloso.alwaysdata.net/aveloso_db";
    private String user = "aveloso";
    private String pass = "Favanola250505..";

    public void addTask(String title, String desc, String date) throws Exception {
        Class.forName("com.mysql.cj.jdbc.Driver");
        try (Connection con = DriverManager.getConnection(url, user, pass)) {
            String sql = "INSERT INTO tasks (title, description, due_date) VALUES (?, ?, ?)";
            PreparedStatement ps = con.prepareStatement(sql);
            ps.setString(1, title);
            ps.setString(2, desc);
            ps.setString(3, date);
            ps.executeUpdate();
        }
    }
}
